from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = 'Create a reception user and add to Receptionist group'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True)
        parser.add_argument('--email', type=str, default='')
        parser.add_argument('--password', type=str, required=True)

    def handle(self, *args, **options):
        username = options['username']
        email = options.get('email') or ''
        password = options['password']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User already exists: {username}'))
            return

        user = User.objects.create_user(username=username, email=email, password=password)
        # Not staff, regular user
        user.is_staff = False
        user.save()

        group, _ = Group.objects.get_or_create(name='Receptionist')
        user.groups.add(group)
        user.save()

        self.stdout.write(self.style.SUCCESS(f'Created user {username} and added to group Receptionist'))
