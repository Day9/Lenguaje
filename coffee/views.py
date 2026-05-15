from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
        Reserva.objects.create(
            usuario=request.user,
            servicio=servicio,
            fecha=fecha,
            hora=hora,
        )
        messages.success(request, f"Cita solicitada para {servicio.name} el {fecha} a las {hora}.")
        return redirect('perfil')
    return render(request, 'detalle.html', {'servicio': servicio})


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
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        fecha = request.POST.get('date')
        hora = request.POST.get('time')
        Reserva.objects.create(
            usuario=request.user,
            servicio=servicio,
            fecha=fecha,
            hora=hora,
        )
        messages.success(request, f"Cita solicitada para {servicio.name} el {fecha} a las {hora}.")
        return redirect('perfil')
    return render(request, 'book_service.html', {'servicio': servicio})