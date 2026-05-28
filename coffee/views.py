from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import *


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
        return redirect('perfil')
        
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
    reservas = Reserva.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    return render(request, 'perfil.html', {'reservas': reservas})


def register(request):
    if request.method == 'POST':
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
    # Reutiliza la misma lógica robusta de detalle_servicio
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        fecha = request.POST.get('date')
        hora = request.POST.get('time')
        # parse date and time similar to detalle_servicio
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

        Reserva.objects.create(
            usuario=request.user,
            servicio=servicio,
            fecha=fecha_obj,
            hora=hora_solicitada,
            estado='PENDIENTE'
        )
        messages.success(request, f"Cita solicitada para {servicio.name}. En revisión.")
        return redirect('perfil')
    return render(request, 'book_service.html', {'servicio': servicio})