from coffee.models import Reserva
r = Reserva.objects.first()
print('Found', r.id if r else None)
if r:
    r.estado = 'CONFIRMADA' if r.estado != 'CONFIRMADA' else 'RECHAZADA'
    r.save()
    print('Saved', r.id, r.estado)
