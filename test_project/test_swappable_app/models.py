"""Custom model implementations for testing swappable models functionality"""

from django.db import models

from cities.models import BaseCity, BaseContinent, BaseCountry


class CustomContinent(BaseContinent):
    """Custom continent model with extra field for testing"""

    custom_data = models.TextField(blank=True, default="")

    class Meta(BaseContinent.Meta):
        pass


class CustomCountry(BaseCountry):
    """Custom country model with extra field for testing"""

    custom_field = models.CharField(max_length=100, blank=True, default="")
    is_verified = models.BooleanField(default=False)

    class Meta(BaseCountry.Meta):
        pass


class CustomCity(BaseCity):
    """Custom city model with extra fields for testing"""

    custom_population_verified = models.BooleanField(default=False)
    custom_notes = models.TextField(blank=True, default="")

    class Meta(BaseCity.Meta):
        pass


class CustomAlternativeName(models.Model):
    """Custom alternative name model with extra field for testing"""

    # Note: AlternativeName doesn't have a Base class, so we need to replicate fields
    # This is a limitation that might need to be addressed separately
    name = models.CharField(max_length=255)
    language_code = models.CharField(max_length=100)
    is_preferred = models.BooleanField(default=False)
    is_short = models.BooleanField(default=False)
    is_colloquial = models.BooleanField(default=False)
    is_historic = models.BooleanField(default=False)

    # Custom field
    custom_verified = models.BooleanField(default=False)

    class Meta:
        swappable = "CITIES_ALTERNATIVENAME_MODEL"

    def __str__(self):
        return f"{self.name} ({self.language_code})"
