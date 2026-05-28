from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # ÚNICA RUTA PARA EL SERVICIO: Muestra el detalle y procesa la reserva (POST)
    path('servicio/<int:pk>/', views.detalle_servicio, name='detalle'),
    
    # Ruta asíncrona para que el JavaScript consulte las horas libres en tiempo real
    path('servicio/<int:servicio_id>/horas/', views.obtener_horas_disponibles, name='obtener_horas_disponibles'),
    
    path('especialistas/', views.especialistas, name='especialistas'),
    path('perfil/', views.perfil, name='perfil'),

    # Recuperación de contraseñas de Django
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]