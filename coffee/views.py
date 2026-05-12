from django.shortcuts import render, get_object_or_404
from .models import Servicio 

# Vista de la página principal
def index(request):
    return render(request, 'index.html')

#vista del catalogo
def home(request):
    mis_servicios = Servicio.objects.all()  # Nombre de variable más descriptivo
    return render(request, 'home.html', {'lista_servicios': mis_servicios})

# Nueva vista para el detalle del servicio
def detalle_servicio(request, pk):
    # Buscamos el servicio por su ID (pk) usando el nuevo modelo
    servicio = get_object_or_404(Servicio, pk=pk)
    return render(request, 'detalle.html', {'servicio': servicio})

def register(request):
    return render(request, 'register.html')

def login(request):
    return render(request, 'login.html')