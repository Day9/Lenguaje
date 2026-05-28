from django.contrib import admin
from .models import Servicio, Reserva, HorarioTrabajo, Specialist


class ServicioAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quantify')
    filter_horizontal = ('specialists',)


class SpecialistAdmin(admin.ModelAdmin):
    list_display = ('name', 'available')
    list_filter = ('available',)

admin.site.register(Servicio, ServicioAdmin)
admin.site.register(Specialist, SpecialistAdmin)
admin.site.register(HorarioTrabajo)
admin.site.register(Reserva)