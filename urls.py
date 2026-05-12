"""
URL configuration for CoffeeShopp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from coffee import views # Importamos las vistas directamente


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. EL INDEX
    path('', views.index, name='index'), 
    
    # 2. EL REGISTRO 
    path('register/', views.register, name='register'),
    
    # 3. EL LOGIN
    path('login/', views.login, name='login'),
    
    # 4. EL CATÁLOGO
    path('catalogo/', views.home, name='home'),

    # 5. EL DETALLE 
    path('servicio/<int:pk>/', views.detalle_servicio, name='detalle'),
]