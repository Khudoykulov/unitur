"""Machine-translate dashboard content into every site language.

When staff save a record from the dashboard they type it in one language; this
fills the remaining ``modeltranslation`` language fields automatically via
Google Translate (deep-translator). It is best-effort: any field/language that
fails to translate is left untouched so a save never breaks because of the
network.
"""

import logging

from django.conf import settings
from django.utils.translation import get_language
from modeltranslation.translator import NotRegistered, translator

logger = logging.getLogger("dashboard")

# deep-translator's free Google endpoint caps a single request at 5000 chars.
_MAX_LEN = 4500


def _translated_fields(model):
    try:
        opts = translator.get_options_for_model(model)
    except NotRegistered:
        return []
    # ``fields`` is a tuple of original field names in some modeltranslation
    # versions and a {field: {localized fields}} dict in others.
    fields = opts.fields
    if isinstance(fields, dict):
        return list(fields.keys())
    return list(fields)


def autofill_translations(instance, source_lang=None, overwrite=True, force=False):
    """Translate ``instance``'s registered fields from the source language
    into all other site languages and persist the result.

    No-op when ``settings.AUTO_TRANSLATE`` is False (e.g. during tests) unless
    ``force`` is set (used by the bulk management command). When ``overwrite``
    is False, target languages that already have a value are left untouched —
    useful for resumable bulk runs. Returns the number of fields translated.
    """
    if not force and not getattr(settings, "AUTO_TRANSLATE", False):
        return 0

    fields = _translated_fields(type(instance))
    if not fields:
        return 0

    # The dashboard runs in the staff member's chosen UI language, so whatever
    # they typed is in that language.
    src = (source_lang or get_language() or settings.LANGUAGE_CODE).split("-")[0]
    targets = [code for code, _ in settings.LANGUAGES if code != src]
    if not targets:
        return 0

    try:
        from deep_translator import GoogleTranslator
    except ImportError:  # pragma: no cover - dependency missing
        logger.warning("deep-translator not installed; skipping auto-translation")
        return 0

    count = 0
    for field in fields:
        source_value = getattr(instance, f"{field}_{src}", None) or getattr(instance, field, None)
        if not source_value:
            continue
        source_value = str(source_value)
        if len(source_value) > _MAX_LEN:
            # Too long for the free endpoint; skip rather than risk an error.
            continue
        for lang in targets:
            attr = f"{field}_{lang}"
            if not overwrite and getattr(instance, attr, None):
                continue
            try:
                # 'auto' lets Google detect the real language of the text, so
                # it works even if the typed language differs from the UI one.
                result = GoogleTranslator(source="auto", target=lang).translate(source_value)
            except Exception as exc:  # noqa: BLE001 - best effort, never fatal
                logger.warning("auto-translate %s -> %s failed: %s", field, lang, exc)
                continue
            if result:
                setattr(instance, attr, result)
                count += 1

    if count:
        instance.save()
    return count


class AutoTranslateMixin:
    """Run :func:`autofill_translations` on ``self.object`` after a successful
    create/edit in a dashboard CBV.
    """

    def form_valid(self, form):
        response = super().form_valid(form)
        if getattr(self, "object", None) is not None:
            autofill_translations(self.object)
        return response
