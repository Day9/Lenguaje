from django.test import Client
from django.contrib.auth.models import User, Group
from coffee.models import Reserva, Servicio
from datetime import date, time

# Create or get receptionist user
# Ensure receptionist user exists and has staff/group privileges
u, created = User.objects.get_or_create(username='test_reception')
u.email = 'reception@test.local'
u.set_password('testpass123')
u.is_staff = True
u.is_active = True
u.save()
# Ensure group exists and add user
g, _ = Group.objects.get_or_create(name='Receptionist')
u.groups.add(g)

# Create or get customer user
cust, created = User.objects.get_or_create(username='test_customer')
if created:
    cust.email = 'customer@test.local'
    cust.set_password('custpass123')
    cust.save()

# Create servicio if none exists
serv = Servicio.objects.first()
if not serv:
    serv = Servicio.objects.create(name='Test Service', price=10.0, quantify=30, image='', categoria='FACIAL')

# Create a pending reserva
res = Reserva.objects.create(usuario=cust, servicio=serv, fecha=date.today(), hora=time(9,0), estado='PENDIENTE')
print('Reserva created', res.id, res.estado)

# Use test client to login and post approval
c = Client()
# Use force_login to avoid dealing with password hashing/login backend in this test environment
c.force_login(u)
print('Force login done')
resp = c.post(f'/spa/reserva/{res.id}/aprobar/', follow=True)
print('POST status code:', resp.status_code)
res.refresh_from_db()
print('Reserva estado after POST:', res.estado)
print('Redirect chain:', resp.redirect_chain)
