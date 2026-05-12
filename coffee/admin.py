from django.contrib import admin
from .models import Servicio


class CoffeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quantify')




admin.site.register(Servicio, CoffeeAdmin)