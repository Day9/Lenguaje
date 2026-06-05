from django.urls import path
from . import views

urlpatterns = [
    # ====== RUTAS PRINCIPALES DEL SPA SIRENE ======
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
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
    # Role-specific dashboards
    path('reception/', views.reception_dashboard, name='reception_dashboard'),
    path('reserva/<int:reserva_id>/aprobar/', views.aprobar_reserva, name='aprobar_reserva'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    # Admin panel CRUD
    path('admin-panel/specialists/', views.admin_specialists_list, name='admin_specialists_list'),
    path('admin-panel/specialists/add/', views.admin_specialist_create, name='admin_specialist_create'),
    path('admin-panel/specialists/<int:pk>/edit/', views.admin_specialist_edit, name='admin_specialist_edit'),
    path('admin-panel/specialists/<int:pk>/delete/', views.admin_specialist_delete, name='admin_specialist_delete'),

    path('admin-panel/services/', views.admin_services_list, name='admin_services_list'),
    path('admin-panel/services/add/', views.admin_service_create, name='admin_service_create'),
    path('admin-panel/services/<int:pk>/edit/', views.admin_service_edit, name='admin_service_edit'),
    path('admin-panel/services/<int:pk>/delete/', views.admin_service_delete, name='admin_service_delete'),

    path('admin-panel/horarios/', views.admin_horarios_list, name='admin_horarios_list'),
    path('admin-panel/horarios/add/', views.admin_horario_create, name='admin_horario_create'),
    path('admin-panel/horarios/<int:pk>/edit/', views.admin_horario_edit, name='admin_horario_edit'),
    path('admin-panel/horarios/<int:pk>/delete/', views.admin_horario_delete, name='admin_horario_delete'),

    path('admin-panel/reservas/', views.admin_reservas_list, name='admin_reservas_list'),
    path('admin-panel/resumen/pdf/', views.admin_resumen_pdf, name='admin_resumen_pdf'),
    path('admin-panel/users/', views.admin_users_list, name='admin_users_list'),
    path('admin-panel/users/<int:pk>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('reserva/<int:pk>/cambiar-estado/', views.cambiar_estado_reserva, name='cambiar_estado_reserva'),
    path('tratamiento/purificante/', views.tratamiento_purificante, name='tratamiento_purificante'),
    # Páginas legales y de contacto
    path('aviso-legal/', views.aviso_legal, name='aviso_legal'),
    path('politica-privacidad/', views.politica_privacidad, name='politica_privacidad'),
    path('politica-cookies/', views.politica_cookies, name='politica_cookies'),
    path('redes-sociales/', views.redes_sociales, name='redes_sociales'),
    path('terminos-y-condiciones/', views.terminos, name='terminos'),
    path('politica-cancelacion/', views.politica_cancelacion, name='politica_cancelacion'),
    path('politica-reservas/', views.politica_reservas, name='politica_reservas'),
    path('contacto/', views.contacto, name='contacto'),
    path('normas-de-convivencia/', views.normas_convivencia, name='normas_convivencia'),
    path('reserva/<int:pk>/respond/<uuid:token>/', views.specialist_respond, name='specialist_respond'),
    path('reserva/<int:pk>/notify-specialist/', views.notify_specialist, name='notify_specialist'),
]