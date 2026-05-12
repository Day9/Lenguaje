from django.urls import path
from . import views

urlpatterns = [
    # 1. El INDEX (La página de bienvenida)
    path('', views.index, name='index'), 
    
    # 2. El REGISTRO 
    path('register/', views.register, name='register'),
    
    # 3. El CATÁLOGO 
    path('home/', views.home, name='home'), 
    
    # 4. El LOGIN 
    path('login/', views.login, name='login'),
    
    # 5. DETALLE 
    path('servicio/<int:pk>/', views.detalle_servicio, name='detalle'),
]