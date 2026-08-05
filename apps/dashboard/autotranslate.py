"""Machine-translate dashboard content into every site language in background threads.

When staff save a record from the dashboard, Django saves the record instantly (<50ms)
and triggers a background thread to translate the fields automatically via Google Translate.
"""

import logging
import threading

from django.conf import settings
from django.utils.translation import get_language
from modeltranslation.translator import NotRegistered, translator

logger = logging.getLogger("dashboard")

# deep-translator's free Google endpoint caps a single request at 4500 chars.
_MAX_LEN = 4500


def _translated_fields(model):
    try:
        opts = translator.get_options_for_model(model)
    except NotRegistered:
        return []
    fields = opts.fields
    if isinstance(fields, dict):
        return list(fields.keys())
    return list(fields)


def _do_autofill(instance_pk, model_class, source_lang=None, overwrite=True, force=False):
    """Worker function executed in background thread or synchronous bulk runs."""
    try:
        instance = model_class.objects.get(pk=instance_pk)
    except Exception as err:
        logger.warning("auto-translate: model instance not found: %s", err)
        return

    if not force and not getattr(settings, "AUTO_TRANSLATE", False):
        return

    fields = _translated_fields(type(instance))
    if not fields:
        return

    src = str(source_lang or settings.LANGUAGE_CODE).split("-")[0]
    targets = [code for code, _ in settings.LANGUAGES if code != src]
    if not targets:
        return

    try:
        from deep_translator import GoogleTranslator
    except ImportError:  # pragma: no cover
        logger.warning("deep-translator not installed; skipping auto-translation")
        return

    count = 0
    for field in fields:
        source_value = getattr(instance, f"{field}_{src}", None) or getattr(instance, field, None)
        if not source_value:
            continue
        source_value = str(source_value).strip()
        if not source_value or len(source_value) > _MAX_LEN:
            continue
        for lang in targets:
            attr = f"{field}_{lang}"
            existing_val = getattr(instance, attr, None)
            if not overwrite and existing_val and str(existing_val).strip():
                continue
            try:
                result = GoogleTranslator(source="auto", target=lang).translate(source_value)
            except Exception as exc:  # noqa: BLE001
                logger.warning("auto-translate %s -> %s failed: %s", field, lang, exc)
                continue
            if result:
                setattr(instance, attr, result)
                count += 1

    if count:
        instance.save()


def autofill_translations(instance, source_lang=None, overwrite=True, force=False):
    """Translate ``instance``'s registered fields asynchronously.

    Returns immediately so HTTP response is instant (< 50ms).
    """
    if instance is None or not getattr(instance, "pk", None):
        return 0

    if source_lang is None:
        try:
            source_lang = str(get_language() or settings.LANGUAGE_CODE).split("-")[0]
        except Exception:
            source_lang = settings.LANGUAGE_CODE

    if force or getattr(settings, "TESTING", False):
        _do_autofill(instance.pk, type(instance), source_lang, overwrite, force=force)
        return 1

    thread = threading.Thread(
        target=_do_autofill,
        args=(instance.pk, type(instance), source_lang, overwrite, force),
        daemon=True,
    )
    thread.start()
    return 1


class AutoTranslateMixin:
    """Run :func:`autofill_translations` on ``self.object`` after a successful
    create/edit in a dashboard CBV.
    """

    def form_valid(self, form):
        response = super().form_valid(form)
        if getattr(self, "object", None) is not None:
            lang = getattr(self.request, "LANGUAGE_CODE", None) or get_language()
            autofill_translations(self.object, source_lang=lang, overwrite=False)
        return response
