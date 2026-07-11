"""Bulk machine-translate existing content into every site language.

One-off / occasional command to back-fill translations for records created
before auto-translation existed (or imported via seed data).

Examples:
    python manage.py translate_content                 # only-empty, all models
    python manage.py translate_content --overwrite     # re-translate everything
    python manage.py translate_content --models tours.Tour destinations.City
    python manage.py translate_content --source en --sleep 0.3
"""

import time

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand, CommandError
from modeltranslation.translator import translator

from apps.dashboard.autotranslate import autofill_translations


class Command(BaseCommand):
    help = "Translate existing content into all site languages (deep-translator)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite", action="store_true",
            help="Re-translate fields even if a translation already exists.",
        )
        parser.add_argument(
            "--models", nargs="+", default=None, metavar="app_label.Model",
            help="Limit to specific models (default: all translated models).",
        )
        parser.add_argument(
            "--source", default=None,
            help="Source language code of the existing text (default: project default, e.g. en).",
        )
        parser.add_argument(
            "--sleep", type=float, default=0.0,
            help="Seconds to pause between records (helps avoid rate limits).",
        )
        parser.add_argument(
            "--limit", type=int, default=None,
            help="Process at most N records per model (for testing).",
        )

    def _models(self, requested):
        # Skip proxies: they share a table with their concrete model, so the
        # rows are already covered (e.g. DomesticCity -> City).
        registered = [m for m in translator.get_registered_models() if not m._meta.proxy]
        if not requested:
            return registered
        by_label = {m._meta.label.lower(): m for m in registered}
        chosen = []
        for label in requested:
            model = by_label.get(label.lower())
            if model is None:
                raise CommandError(
                    f"'{label}' is not a translated model. Choose from: "
                    + ", ".join(sorted(m._meta.label for m in registered))
                )
            chosen.append(model)
        return chosen

    def handle(self, *args, **opts):
        models = self._models(opts["models"])
        overwrite = opts["overwrite"]
        source = opts["source"]
        sleep = opts["sleep"]
        limit = opts["limit"]

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Translating {len(models)} model(s) "
            f"({'overwrite' if overwrite else 'only-empty'})…"
        ))

        grand_records, grand_fields = 0, 0
        for model in models:
            qs = model.objects.all()
            if limit:
                qs = qs[:limit]
            total = qs.count()
            self.stdout.write(f"\n{model._meta.label} — {total} record(s)")
            changed_records = 0
            for i, obj in enumerate(qs.iterator(), start=1):
                try:
                    n = autofill_translations(
                        obj, source_lang=source, overwrite=overwrite, force=True
                    )
                except Exception as exc:  # noqa: BLE001 - keep going on errors
                    self.stderr.write(self.style.WARNING(f"  ! {obj!r}: {exc}"))
                    n = 0
                if n:
                    changed_records += 1
                    grand_fields += n
                self.stdout.write(f"  [{i}/{total}] {str(obj)[:50]} → {n} field(s)")
                if sleep:
                    time.sleep(sleep)
            grand_records += changed_records
            self.stdout.write(self.style.SUCCESS(
                f"  {changed_records}/{total} record(s) updated"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone — {grand_fields} field(s) translated across {grand_records} record(s)."
        ))
