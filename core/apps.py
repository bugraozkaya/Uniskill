# core/apps.py

from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    # This function is crucial! It loads the signals when the app starts.
    def ready(self):
        import core.signals