from django import forms
from .models import Specialist, Servicio, HorarioTrabajo

from django.contrib.auth.models import User


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class SpecialistForm(forms.ModelForm):
    class Meta:
        model = Specialist
        fields = ['name', 'available', 'email']


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['name', 'price', 'quantify', 'image', 'categoria', 'description', 'specialists']


class HorarioTrabajoForm(forms.ModelForm):
    class Meta:
        model = HorarioTrabajo
        fields = ['dia_semana', 'hora_inicio', 'hora_fin']
