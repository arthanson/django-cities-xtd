"""Tests for data import commands with swappable models"""


import swapper
from django.core.management import call_command
from django.test import TestCase, override_settings


@override_settings(
    CITIES_CONTINENT_MODEL="test_swappable_app.CustomContinent",
    CITIES_COUNTRY_MODEL="test_swappable_app.CustomCountry",
    CITIES_CITY_MODEL="test_swappable_app.CustomCity",
)
class ImportWithCustomModelsTest(TestCase):
    """Test data import with custom models"""

    def setUp(self):
        """Load swapped models"""
        self.Continent = swapper.load_model("cities", "Continent")
        self.Country = swapper.load_model("cities", "Country")
        self.City = swapper.load_model("cities", "City")

    def test_import_countries_custom_model(self):
        """Import countries into custom model"""
        # Import a subset of countries for testing
        call_command("cities", "--import=country", "--quiet")

        # Verify countries were imported into custom model
        countries = self.Country.objects.all()
        self.assertGreater(countries.count(), 0)

        # Verify it's actually the custom model
        first_country = countries.first()
        self.assertIsInstance(first_country, self.Country)
        self.assertEqual(first_country.__class__.__name__, "CustomCountry")

        # Verify custom fields exist and are accessible
        self.assertTrue(hasattr(first_country, "custom_field"))
        self.assertTrue(hasattr(first_country, "is_verified"))

    def test_import_cities_custom_model(self):
        """Import cities into custom model"""
        # Import countries first (cities depend on countries)
        call_command("cities", "--import=country,region,subregion,city", "--quiet")

        # Verify cities were imported into custom model
        cities = self.City.objects.all()
        self.assertGreater(cities.count(), 0)

        # Verify it's actually the custom model
        first_city = cities.first()
        self.assertIsInstance(first_city, self.City)
        self.assertEqual(first_city.__class__.__name__, "CustomCity")

        # Verify custom fields exist and are accessible
        self.assertTrue(hasattr(first_city, "custom_population_verified"))
        self.assertTrue(hasattr(first_city, "custom_notes"))

        # Verify relationships work with swapped models
        self.assertIsNotNone(first_city.country)
        self.assertIsInstance(first_city.country, self.Country)

    def test_custom_fields_default_values_on_import(self):
        """Verify custom fields get default values on import"""
        # Import countries
        call_command("cities", "--import=country", "--quiet")

        country = self.Country.objects.first()

        # Custom fields should have default values
        self.assertEqual(country.custom_field, "")
        self.assertFalse(country.is_verified)

    def test_import_alternative_names_with_swapped_models(self):
        """Test importing alternative names works with swapped models"""
        # Import countries and alternative names
        call_command("cities", "--import=country,alt_name", "--quiet")

        # Load AlternativeName (may or may not be swapped)
        AlternativeName = swapper.load_model("cities", "AlternativeName")

        # Verify alternative names were imported
        alt_names = AlternativeName.objects.all()
        self.assertGreater(alt_names.count(), 0)

        # Verify countries have alternative names (tests the M2M relationship)
        countries_with_alt_names = self.Country.objects.filter(alt_names__isnull=False).distinct()
        self.assertGreater(countries_with_alt_names.count(), 0)

        # Verify we can access alternative names through the relationship
        country_with_alts = countries_with_alt_names.first()
        self.assertGreater(country_with_alts.alt_names.count(), 0)


@override_settings(
    CITIES_CONTINENT_MODEL="test_swappable_app.CustomContinent",
    CITIES_COUNTRY_MODEL="test_swappable_app.CustomCountry",
)
class ReimportWithCustomFieldsTest(TestCase):
    """Test that custom field data persists through re-imports"""

    def setUp(self):
        """Load swapped models"""
        self.Country = swapper.load_model("cities", "Country")

    def test_custom_fields_preserved_on_reimport(self):
        """Verify custom field data not lost on re-import"""
        # Initial import
        call_command("cities", "--import=country", "--quiet")

        # Get a country and add custom data
        country = self.Country.objects.first()
        original_name = country.name
        country.custom_field = "Important custom data"
        country.is_verified = True
        country.save()

        # Re-import (should update existing records)
        call_command("cities", "--import=country", "--quiet")

        # Reload the country
        country.refresh_from_db()

        # Standard fields should be updated/maintained by import
        self.assertEqual(country.name, original_name)

        # Custom fields should be preserved
        self.assertEqual(country.custom_field, "Important custom data")
        self.assertTrue(country.is_verified)


@override_settings(
    CITIES_CITY_MODEL="test_swappable_app.CustomCity",
)
class PartialSwapTest(TestCase):
    """Test swapping only some models (not all)"""

    def setUp(self):
        """Load models"""
        self.Country = swapper.load_model("cities", "Country")
        self.City = swapper.load_model("cities", "City")

    def test_mixed_swapped_and_default_models(self):
        """Test that swapping only City works with default Country"""
        # Import data
        call_command("cities", "--import=country,region,subregion,city", "--quiet")

        # Country should be default model
        country = self.Country.objects.first()
        self.assertEqual(country.__class__.__name__, "Country")
        self.assertEqual(country._meta.app_label, "cities")

        # City should be custom model
        city = self.City.objects.first()
        self.assertEqual(city.__class__.__name__, "CustomCity")
        self.assertEqual(city._meta.app_label, "test_swappable_app")

        # Relationship should work between swapped and non-swapped models
        self.assertIsNotNone(city.country)
        self.assertEqual(city.country.__class__.__name__, "Country")
