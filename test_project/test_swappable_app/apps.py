"""App configuration for test_swappable_app"""

from django.apps import AppConfig


class TestSwappableAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "test_swappable_app"
    label = "test_swappable_app"
