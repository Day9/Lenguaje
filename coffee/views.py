from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import *
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST

# Imports específicos y compatibles con Django 6 para el reset de contraseña
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetView
from django.contrib.auth.forms import PasswordResetForm  # 🌟 IMPORTACIÓN REPARADA AQUÍ
from django.urls import reverse_lazy
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from .forms import SpecialistForm, ServicioForm, HorarioTrabajoForm
from .forms import UserProfileForm
from django.db.models import Count
from django.http import HttpResponse
from django.contrib.auth.models import User

def staff_required(view_func):
    from functools import wraps
    from django.core.exceptions import PermissionDenied
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped


def index(request):
    return render(request, 'index.html')


def home(request):
    categoria = request.GET.get('categoria')
    lista_servicios = Servicio.objects.all()
    if categoria in ['FACIAL', 'CORPORAL']:
        lista_servicios = lista_servicios.filter(categoria=categoria)
    return render(request, 'home.html', {
        'lista_servicios': lista_servicios,
        'categoria': categoria,
    })


def detalle_servicio(request, pk):

    servicio = get_object_or_404(Servicio, pk=pk)
    
    if request.method == 'POST' and request.user.is_authenticated:
        # No permitir que usuarios administradores (staff/superuser) o recepcionistas creen reservas
        if request.user.is_staff or request.user.is_superuser or in_group(request.user, 'Receptionist'):
            messages.error(request, "Esta cuenta no puede crear reservas. Usa una cuenta de cliente.")
            return redirect('home')
        fecha = request.POST.get('date')
        hora = request.POST.get('time')
        specialist_id = request.POST.get('specialist')
        specialist = None

        if specialist_id:
            specialist = get_object_or_404(Specialist, pk=specialist_id)
            if not servicio.specialists.filter(pk=specialist.pk).exists():
                messages.error(request, "El especialista seleccionado no está asignado a este servicio.")
                return render(request, 'detalle.html', {'servicio': servicio})

        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        # Normalize and parse time values coming from the frontend.
        hora_str = (hora or '').strip()
        hora_solicitada = None
        low = hora_str.lower()
        if 'a.m' in low or 'p.m' in low or 'am' in low or 'pm' in low:
            # convert forms like '08:00 a.m.' or '8:00 pm' to '08:00 AM' / '08:00 PM'
            normalized = hora_str.replace('.', '')
            normalized = normalized.replace('a.m', 'AM').replace('p.m', 'PM')
            normalized = normalized.replace('am', 'AM').replace('pm', 'PM')
            hora_solicitada = datetime.strptime(normalized, '%I:%M %p').time()
        else:
            try:
                hora_solicitada = datetime.strptime(hora_str, '%H:%M').time()
            except ValueError:
                # fallback: try parsing as 12-hour without explicit AM/PM
                hora_solicitada = datetime.strptime(hora_str, '%I:%M').time()
        duracion_solicitada = servicio.quantify + 40
        inicio_solicitado = datetime.combine(fecha_obj, hora_solicitada)
        fin_solicitado = inicio_solicitado + timedelta(minutes=duracion_solicitada)

        if specialist:
            especialista_ocupado = Reserva.objects.filter(
                fecha=fecha_obj,
                hora=hora_solicitada,
                especialista=specialist,
                estado='CONFIRMADA'
            ).exists()
            if especialista_ocupado:
                messages.error(request, "El especialista seleccionado ya tiene una cita confirmada en esa hora.")
                return render(request, 'detalle.html', {'servicio': servicio})

        reservas_usuario = Reserva.objects.filter(usuario=request.user, fecha=fecha_obj, estado='CONFIRMADA')
        for res_usuario in reservas_usuario:
            inicio_existente = datetime.combine(fecha_obj, res_usuario.hora)
            fin_existente = inicio_existente + timedelta(minutes=res_usuario.servicio.quantify + 40)
            if not (fin_solicitado <= inicio_existente or inicio_solicitado >= fin_existente):
                messages.error(request, "Tiene otra cita confirmada que se superpone con este horario.")
                return render(request, 'detalle.html', {'servicio': servicio})

        Reserva.objects.create(
            usuario=request.user,
            servicio=servicio,
            especialista=specialist,
            fecha=fecha_obj,
            hora=hora_solicitada,
            estado='PENDIENTE'
        )
        messages.success(request, f"Cita solicitada para {servicio.name}. Queda sujeta a revisión.")
        return redirect('mis_reservas')  # 🌟 MODIFICADO: Te lleva directo al apartado de tus citas
        
    return render(request, 'detalle.html', {'servicio': servicio})


def obtener_horas_disponibles(request, servicio_id):
    fecha_str = request.GET.get('fecha')
    if not fecha_str:
        return JsonResponse({'horas': []})

    try:
        fecha_elegida = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'horas': []}, status=400)

    servicio = get_object_or_404(Servicio, pk=servicio_id)

    weekday_python = fecha_elegida.weekday()
    dia_modelo = weekday_python + 1 if weekday_python < 6 else 0

    horario = HorarioTrabajo.objects.filter(dia_semana=dia_modelo).first()
    if not horario:
        return JsonResponse({'horas': [], 'mensaje': 'El centro médico / Spa se encuentra cerrado este día.'})

    def normalize(text):
        return ''.join(
            ch for ch in (text or '').lower()
            if ch.isalpha() or ch.isspace()
        ).strip()

    servicio_nombre = normalize(servicio.name or servicio.categoria)
    if 'descontracturante' in servicio_nombre:
        bloque_tipo = 'descontracturante'
    elif 'piedra' in servicio_nombre or 'volcan' in servicio_nombre:
        bloque_tipo = 'piedras'
    else:
        bloque_tipo = 'facial'

    bloques_por_dia = {
        'facial': {
            'lunes_jueves': ['08:00 a.m.', '09:40 a.m.', '11:20 a.m.', '01:00 p.m.', '02:40 p.m.', '04:20 p.m.'],
            'viernes_sabado': ['08:00 a.m.', '09:40 a.m.', '11:20 a.m.', '01:00 p.m.', '02:40 p.m.', '04:20 p.m.'],
            'domingo': ['08:00 a.m.', '09:40 a.m.', '11:20 a.m.', '01:00 p.m.', '02:40 p.m.'],
        },
        'descontracturante': {
            'lunes_jueves': ['08:00 a.m.', '09:50 a.m.', '11:40 a.m.', '01:30 p.m.', '03:20 p.m.'],
            'viernes_sabado': ['08:00 a.m.', '09:50 a.m.', '11:40 a.m.', '01:30 p.m.', '03:20 p.m.', '05:10 p.m.'],
            'domingo': ['08:00 a.m.', '09:50 a.m.', '11:40 a.m.', '01:30 p.m.'],
        },
        'piedras': {
            'lunes_jueves': ['08:00 a.m.', '09:30 a.m.', '11:00 a.m.', '12:30 p.m.', '02:00 p.m.', '03:30 p.m.', '05:00 p.m.'],
            'viernes_sabado': ['08:00 a.m.', '09:30 a.m.', '11:00 a.m.', '12:30 p.m.', '02:00 p.m.', '03:30 p.m.', '05:00 p.m.', '06:30 p.m.'],
            'domingo': ['08:00 a.m.', '09:30 a.m.', '11:00 a.m.', '12:30 p.m.', '02:00 p.m.', '03:30 p.m.'],
        },
    }

    if weekday_python <= 3:
        dia_clasificacion = 'lunes_jueves'
    elif weekday_python <= 5:
        dia_clasificacion = 'viernes_sabado'
    else:
        dia_clasificacion = 'domingo'

    bloques = bloques_por_dia[bloque_tipo][dia_clasificacion]

    def slot_to_time(hora_texto):
        normalized = hora_texto.replace('.', '').replace('a.m', 'AM').replace('p.m', 'PM')
        return datetime.strptime(normalized, '%I:%M %p').time()

    slot_tiempos = [slot_to_time(hora) for hora in bloques]

    available_specialists = servicio.specialists.filter(available=True)
    max_parallel = max(1, available_specialists.count())

    reservas_confirmadas = Reserva.objects.filter(fecha=fecha_elegida, servicio=servicio, estado='CONFIRMADA')
    horas_disponibles = []

    for hora_texto, hora_time in zip(bloques, slot_tiempos):
        reservas_mismo_bloque = reservas_confirmadas.filter(hora=hora_time).count()
        if reservas_mismo_bloque >= max_parallel:
            continue

        if request.user.is_authenticated:
            comienzo_slot = datetime.combine(fecha_elegida, hora_time)
            reservas_usuario = reservas_confirmadas.filter(usuario=request.user)
            for res_usuario in reservas_usuario:
                inicio_usuario = datetime.combine(fecha_elegida, res_usuario.hora)
                fin_usuario = inicio_usuario + timedelta(minutes=res_usuario.servicio.quantify + 40)
                if not (comienzo_slot + timedelta(minutes=servicio.quantify + 40) <= inicio_usuario or comienzo_slot >= fin_usuario):
                    break
            else:
                horas_disponibles.append(hora_texto)
        else:
            horas_disponibles.append(hora_texto)

    return JsonResponse({'horas': horas_disponibles})


def especialistas(request):
    lista_especialistas = Servicio.objects.values_list('specialist', flat=True).distinct()
    return render(request, 'especialistas.html', {'especialistas': lista_especialistas})


@login_required
def perfil(request):
    """🌟 MODIFICADO: Muestra única y exclusivamente los datos de la cuenta."""
    return render(request, 'perfil.html')


@login_required
def editar_perfil(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil')
    else:
        form = UserProfileForm(instance=user)
    return render(request, 'perfil_edit.html', {'form': form})


@login_required
def mis_reservas(request):
    """🌟 NUEVO: Apartado exclusivo e independiente para listar las citas."""
    # Solo usuarios clientes (no staff/admin ni recepcionistas) pueden acceder a sus reservas
    if request.user.is_staff or getattr(request.user, 'is_superuser', False) or in_group(request.user, 'Receptionist'):
        raise PermissionDenied
    reservas = Reserva.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    return render(request, 'mis_reservas.html', {'reservas': reservas})


def register(request):
    if request.method == 'POST':
        # Bloquear a administradores para que no puedan reservar
        if request.user.is_staff or getattr(request.user, 'is_superuser', False):
            messages.error(request, "Las cuentas de administrador no pueden crear reservas. Usa una cuenta de cliente.")
            return redirect('home')
        first_name = (request.POST.get('first_name') or '').strip()
        last_name = (request.POST.get('last_name') or '').strip()
        username = (request.POST.get('username') or '').strip()
        email = (request.POST.get('email') or '').strip()
        password = request.POST.get('password') or ''

        user_data_has_error = False

        if not username:
            user_data_has_error = True
            messages.error(request, "El nombre de usuario es obligatorio")
        elif User.objects.filter(username__iexact=username).exists():
            user_data_has_error = True
            messages.error(request, "Nombre de usuario ya existe")

        if not email:
            user_data_has_error = True
            messages.error(request, "El correo electrónico es obligatorio")
        elif User.objects.filter(email__iexact=email).exists():
            user_data_has_error = True
            messages.error(request, "El correo electrónico ya existe")

        if len(password) < 5:
            user_data_has_error = True
            messages.error(request, "La contraseña debe tener al menos 5 caracteres")

        if user_data_has_error:
            return render(request, 'register.html', {
                'first_name': first_name,
                'last_name': last_name,
                'username': username,
                'email': email,
            })

        new_user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )
        new_user.save()
        messages.success(request, "Cuenta creada. Ahora puedes iniciar sesión.")
        return redirect('login')

    return render(request, 'register.html')


def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or 'home'
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect(next_url)
        messages.error(request, "Nombre de usuario o contraseña incorrectos.")

    return render(request, 'login.html', {'next': next_url})


def logout_view(request):
    if request.method == 'POST':
        auth_logout(request)
    return redirect('index')


@login_required
def book_service(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        fecha = request.POST.get('date')
        hora = request.POST.get('time')
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        hora_str = (hora or '').strip()
        low = hora_str.lower()
        if 'a.m' in low or 'p.m' in low or 'am' in low or 'pm' in low:
            normalized = hora_str.replace('.', '')
            normalized = normalized.replace('a.m', 'AM').replace('p.m', 'PM')
            normalized = normalized.replace('am', 'AM').replace('pm', 'PM')
            hora_solicitada = datetime.strptime(normalized, '%I:%M %p').time()
        else:
            try:
                hora_solicitada = datetime.strptime(hora_str, '%H:%M').time()
            except ValueError:
                hora_solicitada = datetime.strptime(hora_str, '%I:%M').time()

        # Evitar que recepcionistas o administradores creen reservas
        if request.user.is_staff or getattr(request.user, 'is_superuser', False) or in_group(request.user, 'Receptionist'):
            messages.error(request, "Esta cuenta no puede crear reservas. Usa una cuenta de cliente.")
            return redirect('home')

        Reserva.objects.create(
            usuario=request.user,
            servicio=servicio,
            fecha=fecha_obj,
            hora=hora_solicitada,
            estado='PENDIENTE'
        )
        messages.success(request, f"Cita solicitada para {servicio.name}. En revisión.")
        return redirect('mis_reservas')  # 🌟 MODIFICADO: También redirige al apartado independiente
    return render(request, 'book_service.html', {'servicio': servicio})


# =====================================================================
#  🌟 COMPONENTES PERSONALIZADOS PARA CONTROL DE CONTRASEÑAS (DJANGO 6) 🌟
# =====================================================================

class FormularioResetPasswordHTML(PasswordResetForm):
    """Fuerza a Django a despachar correos multiparte renderizados con HTML nativo."""
    def save(self, domain_override=None, subject_template_name=None,
             email_template_name=None, use_https=False, token_generator=None,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        
        email_template_name = 'registration/password_reset_email.html'
        html_email_template_name = 'registration/password_reset_email.html'
        
        super().save(
            domain_override=domain_override,
            subject_template_name=subject_template_name,
            email_template_name=email_template_name,
            use_https=use_https,
            token_generator=token_generator,
            from_email=from_email,
            request=request,
            html_email_template_name=html_email_template_name,
            extra_email_context=extra_email_context
        )


class MiPasswordResetView(PasswordResetView):
    """Vista de inicio de recuperación vinculada al formulario HTML forzado."""
    template_name = 'reset_password.html'
    form_class = FormularioResetPasswordHTML
    success_url = reverse_lazy('password_reset_done')


class MiPasswordResetConfirmView(PasswordResetConfirmView):
    """Vista encargada de procesar el nuevo password ingresado por el usuario."""
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


# -------------------------
# Role helpers & dashboards
# -------------------------

def in_group(user, group_name):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=group_name).exists()

def group_required(group_name):
    return user_passes_test(lambda u: in_group(u, group_name))


def recepcionista_required(view_func):
    """Permite acceso solo a `is_staff` o miembros del grupo 'recepcionista' (case-insensitive).
    Lanza PermissionDenied (403) si no tiene acceso.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not user or not user.is_authenticated:
            raise PermissionDenied
        if user.is_staff:
            return view_func(request, *args, **kwargs)
        # comprobar nombres comunes en inglés/español
        groups = [g.lower() for g in user.groups.values_list('name', flat=True)]
        if 'recepcionista' in groups or 'receptionist' in groups:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped


@login_required
@group_required('Receptionist')
def reception_dashboard(request):
    """Panel para recepcionistas: ver y gestionar reservas pendientes."""
    reservas = Reserva.objects.filter(estado='PENDIENTE').order_by('fecha', 'hora')
    return render(request, 'reception_dashboard.html', {'reservas': reservas})


@login_required
@recepcionista_required
def aprobar_reserva(request, reserva_id):
    """Aprobar una reserva (solo POST). Cambia estado 'PENDIENTE' -> 'APROBADO'."""
    if request.method != 'POST':
        raise PermissionDenied
    reserva = get_object_or_404(Reserva, pk=reserva_id)
    if reserva.estado != 'PENDIENTE':
        messages.error(request, 'La reserva no está en estado PENDIENTE.')
        return redirect('reception_dashboard')
    reserva.estado = 'CONFIRMADA'
    reserva.save()
    messages.success(request, 'Reserva aprobada correctamente.')
    return redirect('reception_dashboard')


@login_required
@staff_required
def admin_dashboard(request):
    """Panel para el admin superior: visualizar reservas y resumen estadístico."""
    servicios = Servicio.objects.all().order_by('name')
    especialistas = Specialist.objects.all().order_by('name')
    reservas = Reserva.objects.all()
    # Conteo por estado
    conteos = Reserva.objects.values('estado').annotate(total=Count('id'))
    conteo_dict = {c['estado']: c['total'] for c in conteos}
    return render(request, 'admin_dashboard.html', {
        'servicios': servicios,
        'especialistas': especialistas,
        'reservas': reservas,
        'conteos': conteo_dict,
    })


@login_required
@group_required('AdminSuperior')
def admin_specialists_list(request):
    specialists = Specialist.objects.all().order_by('name')
    return render(request, 'admin/specialists_list.html', {'specialists': specialists})


@login_required
@group_required('AdminSuperior')
def admin_specialist_create(request):
    if request.method == 'POST':
        form = SpecialistForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Especialista creado.')
            return redirect('admin_specialists_list')
    else:
        form = SpecialistForm()
    return render(request, 'admin/specialist_form.html', {'form': form})


@login_required
@group_required('AdminSuperior')
def admin_specialist_edit(request, pk):
    spec = get_object_or_404(Specialist, pk=pk)
    if request.method == 'POST':
        form = SpecialistForm(request.POST, instance=spec)
        if form.is_valid():
            form.save()
            messages.success(request, 'Especialista actualizado.')
            return redirect('admin_specialists_list')
    else:
        form = SpecialistForm(instance=spec)
    return render(request, 'admin/specialist_form.html', {'form': form, 'specialist': spec})


@login_required
@group_required('AdminSuperior')
def admin_specialist_delete(request, pk):
    spec = get_object_or_404(Specialist, pk=pk)
    if request.method == 'POST':
        spec.delete()
        messages.success(request, 'Especialista eliminado.')
        return redirect('admin_specialists_list')
    return render(request, 'admin/specialist_confirm_delete.html', {'specialist': spec})


@login_required
@group_required('AdminSuperior')
def admin_services_list(request):
    servicios = Servicio.objects.all().order_by('name')
    return render(request, 'admin/services_list.html', {'servicios': servicios})


@login_required
@group_required('AdminSuperior')
def admin_service_create(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Servicio creado.')
            return redirect('admin_services_list')
    else:
        form = ServicioForm()
    return render(request, 'admin/service_form.html', {'form': form})


@login_required
@group_required('AdminSuperior')
def admin_service_edit(request, pk):
    serv = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=serv)
        if form.is_valid():
            form.save()
            messages.success(request, 'Servicio actualizado.')
            return redirect('admin_services_list')
    else:
        form = ServicioForm(instance=serv)
    return render(request, 'admin/service_form.html', {'form': form, 'servicio': serv})


@login_required
@group_required('AdminSuperior')
def admin_service_delete(request, pk):
    serv = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        serv.delete()
        messages.success(request, 'Servicio eliminado.')
        return redirect('admin_services_list')
    return render(request, 'admin/service_confirm_delete.html', {'servicio': serv})


@login_required
@group_required('AdminSuperior')
def admin_horarios_list(request):
    horarios = HorarioTrabajo.objects.all().order_by('dia_semana')
    return render(request, 'admin/horarios_list.html', {'horarios': horarios})


@login_required
@group_required('AdminSuperior')
def admin_horario_create(request):
    if request.method == 'POST':
        form = HorarioTrabajoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Horario creado.')
            return redirect('admin_horarios_list')
    else:
        form = HorarioTrabajoForm()
    return render(request, 'admin/horario_form.html', {'form': form})


@login_required
@group_required('AdminSuperior')
def admin_horario_edit(request, pk):
    h = get_object_or_404(HorarioTrabajo, pk=pk)
    if request.method == 'POST':
        form = HorarioTrabajoForm(request.POST, instance=h)
        if form.is_valid():
            form.save()
            messages.success(request, 'Horario actualizado.')
            return redirect('admin_horarios_list')
    else:
        form = HorarioTrabajoForm(instance=h)
    return render(request, 'admin/horario_form.html', {'form': form, 'horario': h})


@login_required
@group_required('AdminSuperior')
def admin_horario_delete(request, pk):
    h = get_object_or_404(HorarioTrabajo, pk=pk)
    if request.method == 'POST':
        h.delete()
        messages.success(request, 'Horario eliminado.')
        return redirect('admin_horarios_list')
    return render(request, 'admin/horario_confirm_delete.html', {'horario': h})


@login_required
@group_required('AdminSuperior')
def admin_reservas_list(request):
    # Mostrar resumen (balance) de reservas para AdminSuperior. Las acciones
    # de aceptar/denegar se realizan desde el panel de Recepción.
    conteos = Reserva.objects.values('estado').annotate(total=Count('id'))
    return render(request, 'admin/reservas_summary.html', {'conteos': conteos})


@login_required
@staff_required
def admin_resumen_pdf(request):
    """Genera un resumen estadístico de reservas y devuelve PDF (si está instalado xhtml2pdf).
    Si no está instalado, devuelve la vista HTML como fallback.
    """
    # Conteo por estado
    conteos = Reserva.objects.values('estado').annotate(total=Count('id'))
    # Conteo por fecha (para la gráfica)
    reservas_por_fecha = Reserva.objects.values('fecha').annotate(total=Count('id')).order_by('fecha')
    contexto = {'conteos': conteos, 'reservas_por_fecha': reservas_por_fecha}

    # Intentar generar una gráfica PNG en memoria con matplotlib y pasarla al template como base64
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import base64
        from io import BytesIO

        fechas = [r['fecha'].strftime('%Y-%m-%d') for r in reservas_por_fecha]
        totales = [r['total'] for r in reservas_por_fecha]

        if fechas:
            fig, ax = plt.subplots(figsize=(max(4, len(fechas) * 0.6), 3))
            ax.bar(fechas, totales, color='#1e6fb8')
            ax.set_xlabel('Fecha')
            ax.set_ylabel('Reservas')
            ax.set_title('Reservas por fecha')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=150)
            plt.close(fig)
            buf.seek(0)
            contexto['chart_base64'] = base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception:
        # matplotlib no disponible o fallo al generar la imagen: seguimos sin la gráfica
        pass

    # Render HTML fallback (para navegador)
    html = render(request, 'admin/resumen_pdf.html', contexto)

    # Para generar PDF con xhtml2pdf usamos una plantilla simplificada
    try:
        from django.template.loader import render_to_string
        from xhtml2pdf import pisa
        from io import BytesIO

        pdf_html = render_to_string('admin/resumen_pdf_pdf.html', contexto)
        pdf_io = BytesIO()
        pisa_status = pisa.CreatePDF(pdf_html.encode('utf-8'), dest=pdf_io)
        if pisa_status.err:
            return HttpResponse('Error generando PDF', status=500)
        pdf_io.seek(0)
        return HttpResponse(pdf_io.read(), content_type='application/pdf')
    except Exception:
        # Fallback: mostrar HTML
        return html


@login_required
@staff_required
def admin_users_list(request):
    # Gestión de usuarios personalizada deshabilitada. Redirigir al Django admin
    try:
        admin_url = reverse('admin:auth_user_changelist')
    except Exception:
        admin_url = '/admin/auth/user/'
    return redirect(admin_url)


@login_required
@staff_required
def admin_user_edit(request, pk):
    # Redirigir al Django admin para edición de usuarios
    try:
        admin_url = reverse('admin:auth_user_change', args=[pk])
    except Exception:
        admin_url = f'/admin/auth/user/{pk}/change/'
    return redirect(admin_url)


@login_required
@group_required('Receptionist')
def cambiar_estado_reserva(request, pk):
    """Endpoint para que la recepcion pueda confirmar/rechazar reservas.
    AdminSuperior también puede usar el admin tradicional en /admin/.
    """
    reserva = get_object_or_404(Reserva, pk=pk)
    if request.method == 'POST':
        nuevo = request.POST.get('estado')
        if nuevo in ['CONFIRMADA', 'RECHAZADA', 'PENDIENTE']:
            reserva.estado = nuevo
            reserva.save()
            messages.success(request, f'Reserva actualizada a {nuevo}')
        else:
            messages.error(request, 'Estado inválido')
    return redirect('reception_dashboard')


@login_required
@group_required('Receptionist')
def notify_specialist(request, pk):
    """Enviar correo manual al especialista asignado para una reserva específica."""
    reserva = get_object_or_404(Reserva, pk=pk)
    if not reserva.especialista or not reserva.especialista.email:
        messages.error(request, 'La reserva no tiene especialista con correo configurado.')
        return redirect('reception_dashboard')

    try:
        asunto = f"Estado de reserva: {reserva.estado} - {reserva.servicio.name}"
        contexto = {
            'reserva': reserva,
            'estado': reserva.estado,
        }
        # Usamos una plantilla simple que informa el estado actual de la reserva
        html_message = render_to_string('registration/correo_estado_especialista.html', contexto)
        plain_message = strip_tags(html_message)
        bcc = getattr(settings, 'NOTIFY_BCC', []) or None
        msg = EmailMultiAlternatives(subject=asunto, body=plain_message, from_email=settings.DEFAULT_FROM_EMAIL, to=[reserva.especialista.email], bcc=bcc)
        msg.attach_alternative(html_message, 'text/html')
        msg.send(fail_silently=True)
        messages.success(request, 'Correo de notificación enviado al especialista.')
    except Exception as e:
        messages.error(request, f'Error enviando correo: {e}')

    return redirect('reception_dashboard')


def tratamiento_purificante(request):
    """Página pública que describe el tratamiento purificante solicitado."""
    descripcion = (
        "Un tratamiento purificante que aprovecha las propiedades remineralizantes de las algas "
        "para desintoxicar el cuerpo y mejorar la salud de la piel. Es una experiencia profunda "
        "que combina el bienestar físico con una renovación cutánea completa."
    )
    return render(request, 'tratamiento_purificante.html', {'descripcion': descripcion})


def aviso_legal(request):
    return render(request, 'aviso_legal.html')


def politica_privacidad(request):
    return render(request, 'politica_privacidad.html')


def politica_cookies(request):
    return render(request, 'politica_cookies.html')


def redes_sociales(request):
    return render(request, 'redes_sociales.html')


def terminos(request):
    return render(request, 'terminos.html')


def politica_cancelacion(request):
    return render(request, 'politica_cancelacion.html')


def politica_reservas(request):
    return render(request, 'politica_reservas.html')


def contacto(request):
    return render(request, 'contacto.html')


def normas_convivencia(request):
    return render(request, 'normas_convivencia.html')


def specialist_respond(request, pk, token):
    """Procesa la respuesta del especialista mediante token en el correo."""
    reserva = get_object_or_404(Reserva, pk=pk)
    try:
        token_val = str(token)
    except Exception:
        token_val = None

    if str(reserva.specialist_token) != token_val:
        return render(request, 'specialist_response.html', {'ok': False, 'msg': 'Token inválido o caducado.'})

    accion = request.GET.get('action')
    if accion == 'accept':
        reserva.specialist_response = 'ACEPTADA'
        reserva.save()
        msg = 'Has aceptado la reserva. El recepcionista finalizará el estado.'
    elif accion == 'reject':
        reserva.specialist_response = 'RECHAZADA'
        reserva.save()
        msg = 'Has rechazado la reserva. El recepcionista será notificado.'
    else:
        return render(request, 'specialist_response.html', {'ok': False, 'msg': 'Acción inválida.'})

    # Notificar al correo de recepción (DEFAULT_FROM_EMAIL) que el especialista respondió
    try:
        asunto = f"Respuesta del especialista para reserva {reserva.id}"
        cuerpo = f"El especialista ha respondido: {reserva.specialist_response} para la reserva {reserva.servicio.name} el {reserva.fecha} a las {reserva.hora}."
        bcc = getattr(settings, 'NOTIFY_BCC', []) or None
        msg = EmailMultiAlternatives(subject=asunto, body=cuerpo, from_email=settings.DEFAULT_FROM_EMAIL, to=[settings.DEFAULT_FROM_EMAIL], bcc=bcc)
        msg.send(fail_silently=True)
    except Exception as e:
        print('Error notificando a recepción:', e)

    return render(request, 'specialist_response.html', {'ok': True, 'msg': msg})