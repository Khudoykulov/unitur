from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'apps.core'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        self._patch_rosetta()

    def _patch_rosetta(self):
        try:
            import rosetta.views as rosetta_views
            original_home = rosetta_views.home

            def patched_home(request, *args, **kwargs):
                response = original_home(request, *args, **kwargs)
                # POST so'rov bo'lsa (save bosilsa) — compile qilamiz
                if request.method == 'POST':
                    _compile_messages()
                return response

            rosetta_views.home = patched_home
        except Exception:
            pass


def _compile_messages():
    import subprocess
    from django.conf import settings
    subprocess.Popen(
        ['python', 'manage.py', 'compilemessages'],
        cwd=str(settings.BASE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )