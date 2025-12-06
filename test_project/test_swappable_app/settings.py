"""Settings for testing swappable models"""

# Import base settings from test_app
from test_app.settings import *  # noqa: F401,F403

# Override INSTALLED_APPS to include test_swappable_app BEFORE cities
# This is important for model swapping to work correctly
INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "test_swappable_app",  # Must come before cities
    "cities.apps.CitiesConfig",
    "model_utils",
    "test_app",
)

# Configure swappable models
CITIES_CONTINENT_MODEL = "test_swappable_app.CustomContinent"
CITIES_COUNTRY_MODEL = "test_swappable_app.CustomCountry"
CITIES_CITY_MODEL = "test_swappable_app.CustomCity"
# Note: AlternativeName swapping will be tested when fully implemented
# CITIES_ALTERNATIVENAME_MODEL = "test_swappable_app.CustomAlternativeName"
