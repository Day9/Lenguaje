from django.urls import path
from . import views

urlpatterns = [
    # ====== RUTAS PRINCIPALES DEL SPA NAUTILUS ======
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Detalle del servicio y procesamiento de la reserva (POST)
    path('servicio/<int:pk>/', views.detalle_servicio, name='detalle'),
    
    # Consulta asíncrona de horas libres en tiempo real mediante JavaScript
    path('servicio/<int:servicio_id>/horas/', views.obtener_horas_disponibles, name='obtener_horas_disponibles'),
    
    path('especialistas/', views.especialistas, name='especialistas'),
    
    # 🌟 AHORA SEPARADOS EN DOS APARTADOS INDEPENDIENTES
    path('perfil/', views.perfil, name='perfil'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
]