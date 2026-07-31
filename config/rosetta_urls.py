from django.urls import include, path
from rosetta.views import TranslationFormView
import sys
import subprocess
from django.conf import settings


class PatchedTranslationFormView(TranslationFormView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        try:
            subprocess.Popen(
                [sys.executable, 'manage.py', 'compilemessages'],
                cwd=str(settings.BASE_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"compilemessages xatosi: {e}")
        return response


# Rosetta URLs ni override qilamiz
from rosetta import urls as rosetta_urls
import rosetta.views as rosetta_views

# Original URL patterns olish
urlpatterns = []
for pattern in rosetta_urls.urlpatterns:
    # TranslationFormView ishlatgan URL'ni almashtiramiz
    if hasattr(pattern, 'callback') and hasattr(pattern.callback, 'view_class'):
        if pattern.callback.view_class == rosetta_views.TranslationFormView:
            urlpatterns.append(
                path(pattern.pattern._route, PatchedTranslationFormView.as_view(), name=pattern.name)
            )
            continue
    urlpatterns.append(pattern)