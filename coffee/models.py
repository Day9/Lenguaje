from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

class Specialist(models.Model):
    name = models.CharField(max_length=255)
    available = models.BooleanField(default=True)

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
        ('CANCELADA', 'Cancelada'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    especialista = models.ForeignKey('Specialist', on_delete=models.PROTECT, null=True, blank=True)
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
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