"""Import the bundled static hero images into the HeroSlide model.

Gives the dashboard a starting set of rotating background images for the Ichki
Turlar page that staff can then replace/reorder/extend. Idempotent.

    python manage.py seed_hero_slides
"""

from django.contrib.staticfiles import finders
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.core.models import HeroSlide


class Command(BaseCommand):
    help = "Seed HeroSlide rows from the bundled static hero images."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Add even if slides already exist.")

    def handle(self, *args, **opts):
        page = "ichki_turlar"
        if HeroSlide.objects.filter(page=page).exists() and not opts["force"]:
            self.stdout.write("Ichki Turlar slides already exist — nothing to do.")
            return

        created = 0
        for i in range(1, 6):
            path = finders.find(f"images/hero-ichki-{i}.jpg")
            if not path:
                continue
            with open(path, "rb") as fh:
                data = fh.read()
            slide = HeroSlide(page=page, order=i, alt=f"Ichki Turlar {i}")
            slide.image.save(f"hero-ichki-{i}.jpg", ContentFile(data), save=True)
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created} hero slide(s) for '{page}'."))
