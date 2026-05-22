from django.apps import AppConfig


class PatrimonioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'patrimonio'
    
    def ready(self):
        """Registrar signals quando app estiver pronto"""
        import patrimonio.signals
