"""
URL configuration for CoffeeShopp project.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from coffee import views as coffee_views  # Importamos tus vistas personalizadas

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 🌟 RUTAS DE AUTENTICACIÓN GLOBALES (Evitan errores NoReverseMatch en plantillas)
    path('login/', coffee_views.login_view, name='login'),
    path('logout/', coffee_views.logout_view, name='logout'),
    
    # 🌟 CORRECCIÓN DE RUTAS: Forzamos el prefijo 'spa/' para que coincida con tu diseño
    path('spa/password-reset/', coffee_views.MiPasswordResetView.as_view(), name='password_reset'),
    
    path('spa/password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('spa/password-reset-confirm/<uidb64>/<token>/', coffee_views.MiPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    path('spa/password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    # Redirigir la raíz a /spa/ para evitar 404 al cargar la aplicación en /
    path('', RedirectView.as_view(url='/spa/')),

    # Tu aplicación principal
    path('spa/', include('coffee.urls')),
]