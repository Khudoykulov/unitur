from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'apps.core'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        self._patch_rosetta()

    def _patch_rosetta(self):
        try:
            from rosetta.views import TranslationFormView
            original_post = TranslationFormView.post

            def patched_post(self, request, *args, **kwargs):
                response = original_post(self, request, *args, **kwargs)
                _compile_messages()
                return response

            TranslationFormView.post = patched_post
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Rosetta patch xatosi: {e}")


def _compile_messages():
    import subprocess
    from django.conf import settings
    subprocess.Popen(
        ['python', 'manage.py', 'compilemessages'],
        cwd=str(settings.BASE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )