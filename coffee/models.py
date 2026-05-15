from django.db import models
from django.contrib.auth.models import User

class Servicio(models.Model):
    CATEGORY_CHOICES = [
        ('FACIAL', 'Faciales'),
        ('CORPORAL', 'Corporales'),
    ]

    name = models.CharField(max_length=255)
    price = models.FloatField()
    quantify = models.IntegerField()
    image = models.CharField(max_length=2083)
    categoria = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='FACIAL')
    description = models.TextField(null=True, blank=True)
    specialist = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'En revisión'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reserva de {self.usuario.username} para {self.servicio.name}"