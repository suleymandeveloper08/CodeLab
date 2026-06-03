from django.apps import AppConfig


class CodelabAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'codelab_app'
    
    def ready(self):
        import codelab_app.signals