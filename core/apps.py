# core/apps.py

from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    # BU FONKSİYONU EKLEMEZSEN SİNYALLER ÇALIŞMAZ!
    def ready(self):
        import core.signals