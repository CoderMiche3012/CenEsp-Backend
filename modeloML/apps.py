from django.apps import AppConfig

class ModelomlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modeloML'

    def ready(self):
        import modeloML.signals 