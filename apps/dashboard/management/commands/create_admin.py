"""Management command: create a superuser with dashboard access."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create a superuser and optionally set up Manager/Operator groups."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--first-name", default="Admin")
        parser.add_argument("--setup-groups", action="store_true",
                            help="Create Manager and Operator permission groups")

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]
        first_name = options["first_name"]

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"User {email} already exists."))
        else:
            user = User.objects.create_superuser(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                is_staff=True,
                is_superuser=True,
            )
            self.stdout.write(self.style.SUCCESS(f"Superuser created: {email}"))

        if options["setup_groups"]:
            for name in ["Manager", "Operator"]:
                group, created = Group.objects.get_or_create(name=name)
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Group '{name}' created."))
                else:
                    self.stdout.write(f"Group '{name}' already exists.")
