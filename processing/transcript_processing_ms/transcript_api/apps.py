from django.apps import AppConfig


class TranscriptApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transcript_api'

    def ready(self):
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            return
        from .services import load_whisper_model
        load_whisper_model()
