from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = 'Create default groups: Receptionist and AdminSuperior'

    def handle(self, *args, **options):
        groups = ['Receptionist', 'AdminSuperior']
        for g in groups:
            group, created = Group.objects.get_or_create(name=g)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Group created: {g}'))
            else:
                self.stdout.write(self.style.WARNING(f'Group already exists: {g}'))
        self.stdout.write(self.style.SUCCESS('Done. Assign users to these groups via the admin interface.'))
