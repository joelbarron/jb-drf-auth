from django.apps import AppConfig

class JbDrfAuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "jb_drf_auth"
    verbose_name = "JB DRF Auth"

    def ready(self):
        from jb_drf_auth import checks  # noqa: F401
