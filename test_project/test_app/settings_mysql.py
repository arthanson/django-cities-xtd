"""MySQL-specific settings for testing django-cities with MySQL + GIS"""

import os

# Import all settings from base
from .settings import *  # noqa: F401,F403

# Override database configuration for MySQL
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.mysql",
        "NAME": os.environ.get("MYSQL_DATABASE", "django_cities"),
        "USER": os.environ.get("MYSQL_USER", "django"),
        "PASSWORD": os.environ.get("MYSQL_PASSWORD", "django"),
        "HOST": os.environ.get("MYSQL_HOST", "127.0.0.1"),
        "PORT": int(os.environ.get("MYSQL_PORT", "3306")),
        "OPTIONS": {
            # MySQL 8.0+ uses caching_sha2_password by default
            # but we're using mysql_native_password in docker-compose
            "charset": "utf8mb4",
        },
        "TEST": {
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_unicode_ci",
        },
    }
}

# MySQL-specific: Use AutoField instead of BigAutoField
# MySQL has issues with BigAutoField in some GIS contexts
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
