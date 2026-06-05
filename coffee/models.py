from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

# Importaciones necesarias para el envío automatizado de correos
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
import threading
import logging

logger = logging.getLogger(__name__)


class Specialist(models.Model):
    name = models.CharField(max_length=255)
    available = models.BooleanField(default=True)
    email = models.EmailField(null=True, blank=True)

    class Meta:
        verbose_name = 'Specialist'
        verbose_name_plural = 'Specialists'

    def __str__(self):
        return self.name


class Servicio(models.Model):
    CATEGORY_CHOICES = [
        ('FACIAL', 'Faciales'),
        ('CORPORAL', 'Corporales'),
    ]

    name = models.CharField(max_length=255)
    price = models.FloatField()
    quantify = models.IntegerField()  # Representa la duración en minutos
    image = models.CharField(max_length=2083)
    categoria = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='FACIAL')
    description = models.TextField(null=True, blank=True)
    specialist = models.CharField(max_length=255, null=True, blank=True)
    specialists = models.ManyToManyField('Specialist', blank=True, related_name='services')

    def __str__(self):
        return self.name


# --- NUEVO MODELO PARA EL CONTROL DEL ADMINISTRADOR ---
class HorarioTrabajo(models.Model):
    DIA_CHOICES = [
        (1, 'Lunes'),
        (2, 'Martes'),
        (3, 'Miércoles'),
        (4, 'Jueves'),
        (5, 'Viernes'),
        (6, 'Sábado'),
        (0, 'Domingo'),
    ]
    
    dia_semana = models.IntegerField(choices=DIA_CHOICES, unique=True)
    hora_inicio = models.TimeField(help_text="Hora de apertura del Spa")
    hora_fin = models.TimeField(help_text="Hora de cierre del Spa")

    class Meta:
        verbose_name = "Horario de Trabajo"
        verbose_name_plural = "Horarios de Trabajo"

    def __str__(self):
        return f"{self.get_dia_semana_display()}: {self.hora_inicio.strftime('%H:%M')} a {self.hora_fin.strftime('%H:%M')}"


class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'En revisión'),
        ('CONFIRMADA', 'Confirmada'),
        ('RECHAZADA', 'Rechazada'),  # Configurado para el sistema de correos
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    especialista = models.ForeignKey('Specialist', on_delete=models.PROTECT, null=True, blank=True)
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    # Respuesta inicial del especialista (no es el estado final que marca la recepción)
    specialist_response = models.CharField(max_length=20, choices=[('PENDIENTE','Pendiente'),('ACEPTADA','Aceptada'),('RECHAZADA','Rechazada')], default='PENDIENTE')
    # Token seguro para que el especialista confirme/rechace sin autenticación web
    specialist_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    @property
    def hora_fin_bloque(self):
        """
        Calcula matemáticamente a qué hora se libera el espacio.
        Duración del servicio (quantify) + 40 minutos de desinfección/limpieza.
        """
        duracion_total = self.servicio.quantify + 40
        combinado = datetime.combine(self.fecha, self.hora)
        tiempo_final = combinado + timedelta(minutes=duracion_total)
        return tiempo_final.time()

    def __str__(self):
        return f"Reserva de {self.usuario.username} para {self.servicio.name} ({self.estado})"

    # 🌟 INTERCEPCIÓN DEL GUARDADO PARA ENVÍO DE CORREOS 🌟
    def save(self, *args, **kwargs):
        # Si la reserva ya existe (es una actualización en el admin), validamos el cambio de estado
        if self.pk:
            reserva_previa = Reserva.objects.get(pk=self.pk)
            
            # Se detona únicamente si el administrador cambia el estado actual
            if reserva_previa.estado != self.estado and self.estado in ['CONFIRMADA', 'RECHAZADA']:
                # Pre-render the email content so it can be sent after DB commit without blocking the request.
                if self.estado == 'CONFIRMADA':
                    asunto = "¡Tu cita ha sido CONFIRMADA! 🎉 - Spa Sirene"
                else:
                    asunto = "Información sobre tu cita - Spa Sirene"

                contexto = {
                    'usuario': self.usuario,
                    'servicio': self.servicio,
                    'especialista': self.especialista,
                    'fecha': self.fecha,
                    'hora': self.hora,
                    'estado': self.estado,
                }

                html_message = render_to_string('registration/correo_reserva_estado.html', contexto)
                plain_message = strip_tags(html_message)

                # Define an async sender that runs after transaction commit
                def _send_email():
                    try:
                        bcc = getattr(settings, 'NOTIFY_BCC', []) or None
                        msg = EmailMultiAlternatives(subject=asunto, body=plain_message, from_email=settings.DEFAULT_FROM_EMAIL, to=[self.usuario.email], bcc=bcc)
                        msg.attach_alternative(html_message, "text/html")
                        msg.send(fail_silently=True)
                        logger.info('Correo de estado enviado a %s para reserva %s', self.usuario.email, self.pk)
                    except Exception as e:
                        logger.exception('Error enviando correo de estado para reserva %s: %s', self.pk, e)

                # Schedule to run after DB transaction commits to avoid sending on rollback
                try:
                    transaction.on_commit(lambda: threading.Thread(target=_send_email, daemon=True).start())
                except Exception as e:
                    logger.exception('No se pudo programar envío de correo post-commit: %s', e)

        # Ejecuta el guardado real en la base de datos de Django
        super().save(*args, **kwargs)


# Enviar correo al especialista cuando se crea una reserva con especialista asignado
@receiver(post_save, sender=Reserva)
def enviar_correo_especialista(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.especialista and instance.especialista.email:
        try:
            asunto = f"Nueva solicitud de reserva: {instance.servicio.name}"
            contexto = {
                'reserva': instance,
                'url_accept': f"{settings.DEFAULT_FROM_EMAIL}"  # placeholder, se reemplaza en html_message
            }

            # Construir link explícito con token para aceptar/rechazar
            base = getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000')
            accept_url = f"{base}/spa/reserva/{instance.id}/respond/{instance.specialist_token}/?action=accept"
            reject_url = f"{base}/spa/reserva/{instance.id}/respond/{instance.specialist_token}/?action=reject"

            html_message = render_to_string('registration/correo_especialista.html', {
                'reserva': instance,
                'accept_url': accept_url,
                'reject_url': reject_url,
            })
            plain_message = strip_tags(html_message)

            bcc = getattr(settings, 'NOTIFY_BCC', []) or None
            msg = EmailMultiAlternatives(subject=asunto, body=plain_message, from_email=settings.DEFAULT_FROM_EMAIL, to=[instance.especialista.email], bcc=bcc)
            msg.attach_alternative(html_message, "text/html")
            msg.send(fail_silently=True)
        except Exception as e:
            print('Error enviando correo al especialista:', e)