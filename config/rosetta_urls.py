import sys
import subprocess
from threading import local
from django.urls import re_path
from django.conf import settings
from rosetta.views import TranslationFormView
import rosetta.urls as rosetta_urls


class PatchedTranslationFormView(TranslationFormView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        try:
            subprocess.run(
                [sys.executable, 'manage.py', 'compilemessages'],
                cwd=str(settings.BASE_DIR),
                timeout=30,
            )
            from django.utils.translation import trans_real
            trans_real._default = None
            trans_real._active = local()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"compile xatosi: {e}")
        return response


urlpatterns = []
for pattern in rosetta_urls.urlpatterns:
    callback = getattr(pattern, 'callback', None)
    view_class = getattr(callback, 'view_class', None)
    if view_class is TranslationFormView:
        urlpatterns.append(
            re_path(pattern.pattern.regex.pattern, PatchedTranslationFormView.as_view(), name=pattern.name)
        )
    else:
        urlpatterns.append(pattern)
