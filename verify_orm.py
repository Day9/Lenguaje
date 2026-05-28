from coffee.models import Specialist, Servicio

print('Specialist table:', Specialist._meta.db_table)
print('Specialist count:', Specialist.objects.count())
print('Servicio table:', Servicio._meta.db_table)
print('Servicio count:', Servicio.objects.count())
servicio = Servicio.objects.first()
print('first servicio:', servicio)
if servicio:
    print('specialists count:', servicio.specialists.count())
    print('specialists first:', list(servicio.specialists.all())[:5])
