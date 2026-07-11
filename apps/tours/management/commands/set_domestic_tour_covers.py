"""Give the seeded domestic tours a cover image.

Each domestic (multi-city) tour is given the cover photo of its signature stop
city (e.g. Samarkand's Registan for the Golden Road). The city photo is *copied*
into the tour's own ``tours/covers/`` file so the two stay decoupled — later
editing a city image won't silently change a tour cover.

Idempotent: a tour that already has a cover, or whose source city has no photo,
is left untouched. Run with::

    python manage.py set_domestic_tour_covers
"""

import os

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.destinations.models import City
from apps.tours.models import Tour

# tour slug -> the stop city whose photo best represents the trip.
SIGNATURE_CITY = {
    "golden-road-of-uzbekistan": "Samarkand",
    "samarkand-bukhara-highlights": "Bukhara",
    "silk-road-explorer": "Samarkand",
    "ancient-khorezm-khiva-bukhara": "Khiva",
    "fergana-valley-discovery": "Fergana",
}


class Command(BaseCommand):
    help = "Set cover images on the seeded domestic tours from their signature city."

    def handle(self, *args, **options):
        set_count = skipped = missing = 0

        for slug, city_name in SIGNATURE_CITY.items():
            tour = Tour.objects.filter(slug=slug).first()
            if tour is None:
                continue
            if tour.cover_image:
                skipped += 1
                self.stdout.write(f"  = already has a cover, skipped: {tour.title}")
                continue

            city = (
                City.objects.filter(name=city_name, cover_image__gt="")
                .exclude(cover_image__isnull=True)
                .first()
            )
            if city is None or not city.cover_image:
                missing += 1
                self.stderr.write(self.style.WARNING(
                    f"  ! no source image for {city_name}; {tour.title} left without a cover"
                ))
                continue

            ext = os.path.splitext(city.cover_image.name)[1] or ".jpg"
            with city.cover_image.open("rb") as fh:
                data = fh.read()
            tour.cover_image.save(f"{slug}-cover{ext}", ContentFile(data), save=True)
            set_count += 1
            self.stdout.write(self.style.SUCCESS(
                f"  + cover set: {tour.title}  ←  {city_name}"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"Done. {set_count} cover(s) set, {skipped} already had one, {missing} without a source."
        ))
