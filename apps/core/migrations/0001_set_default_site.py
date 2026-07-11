"""Point the django.contrib.sites Site at the real host (from SITE_URL).

Without this the Site stays at Django's default "example.com", which leaks
into sitemap.xml / absolute URLs. Domain + name are read from settings
(SITE_URL / SITE_NAME), so each environment gets the correct value.
"""

from urllib.parse import urlparse

from django.conf import settings
from django.db import migrations


def set_site(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    site_id = getattr(settings, "SITE_ID", 1)
    url = getattr(settings, "SITE_URL", "") or ""
    parsed = urlparse(url if "//" in url else "//" + url)
    domain = parsed.netloc or "localhost:8000"
    name = getattr(settings, "SITE_NAME", "UNITUR travel agency")
    Site.objects.update_or_create(id=site_id, defaults={"domain": domain, "name": name})


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
    ]

    operations = [
        migrations.RunPython(set_site, noop),
    ]
