"""Tests for swappable models functionality"""

import os

import swapper
from django.contrib.gis.geos import Point
from django.test import TestCase, override_settings

# Import from test_swappable_app settings which configures swapped models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_swappable_app.settings")


@override_settings(
    CITIES_CONTINENT_MODEL="test_swappable_app.CustomContinent",
    CITIES_COUNTRY_MODEL="test_swappable_app.CustomCountry",
    CITIES_CITY_MODEL="test_swappable_app.CustomCity",
)
class SwappableModelRegistrationTest(TestCase):
    """Test that swappable models are properly registered"""

    def test_continent_model_swapped(self):
        """Verify CITIES_CONTINENT_MODEL setting is respected"""
        Continent = swapper.load_model("cities", "Continent")
        self.assertEqual(Continent.__name__, "CustomContinent")
        self.assertEqual(Continent._meta.app_label, "test_swappable_app")

    def test_country_model_swapped(self):
        """Verify CITIES_COUNTRY_MODEL setting is respected"""
        Country = swapper.load_model("cities", "Country")
        self.assertEqual(Country.__name__, "CustomCountry")
        self.assertEqual(Country._meta.app_label, "test_swappable_app")

    def test_city_model_swapped(self):
        """Verify CITIES_CITY_MODEL setting is respected"""
        City = swapper.load_model("cities", "City")
        self.assertEqual(City.__name__, "CustomCity")
        self.assertEqual(City._meta.app_label, "test_swappable_app")


@override_settings(
    CITIES_CONTINENT_MODEL="test_swappable_app.CustomContinent",
    CITIES_COUNTRY_MODEL="test_swappable_app.CustomCountry",
    CITIES_CITY_MODEL="test_swappable_app.CustomCity",
)
class CustomModelCreationTest(TestCase):
    """Test creating instances of custom models"""

    def setUp(self):
        """Load swapped models"""
        self.Continent = swapper.load_model("cities", "Continent")
        self.Country = swapper.load_model("cities", "Country")
        self.City = swapper.load_model("cities", "City")

    def test_create_custom_continent(self):
        """Create instance of custom continent model"""
        continent = self.Continent.objects.create(
            name="Test Continent",
            slug="test-continent",
            code="TC",
            custom_data="Custom continent data",
        )
        self.assertIsNotNone(continent.id)
        self.assertEqual(continent.name, "Test Continent")
        self.assertEqual(continent.custom_data, "Custom continent data")

    def test_create_custom_country(self):
        """Create instance of custom country model"""
        country = self.Country.objects.create(
            name="Test Country",
            slug="test-country",
            code="TC",
            code3="TST",
            population=1000000,
            phone="123",
            tld=".tc",
            capital="Test Capital",
            postal_code_format="",
            postal_code_regex="",
            custom_field="Custom country field",
            is_verified=True,
        )
        self.assertIsNotNone(country.id)
        self.assertEqual(country.name, "Test Country")
        self.assertEqual(country.custom_field, "Custom country field")
        self.assertTrue(country.is_verified)

    def test_create_custom_city(self):
        """Create instance of custom city model"""
        country = self.Country.objects.create(
            name="Test Country",
            slug="test-country",
            code="TC",
            code3="TST",
            population=1000000,
            phone="123",
            tld=".tc",
            capital="Test Capital",
            postal_code_format="",
            postal_code_regex="",
        )

        city = self.City.objects.create(
            name="Test City",
            slug="1-test-city",
            name_std="Test City",
            location=Point(0, 0),
            population=100000,
            kind="PPLA",
            timezone="UTC",
            country=country,
            custom_population_verified=True,
            custom_notes="Test notes",
        )
        self.assertIsNotNone(city.id)
        self.assertEqual(city.name, "Test City")
        self.assertTrue(city.custom_population_verified)
        self.assertEqual(city.custom_notes, "Test notes")


@override_settings(
    CITIES_CONTINENT_MODEL="test_swappable_app.CustomContinent",
    CITIES_COUNTRY_MODEL="test_swappable_app.CustomCountry",
    CITIES_CITY_MODEL="test_swappable_app.CustomCity",
)
class SwappableModelRelationshipTest(TestCase):
    """Test relationships between swapped models"""

    def setUp(self):
        """Load swapped models and create test data"""
        self.Continent = swapper.load_model("cities", "Continent")
        self.Country = swapper.load_model("cities", "Country")
        self.City = swapper.load_model("cities", "City")

        self.continent = self.Continent.objects.create(
            name="Test Continent", slug="test-continent", code="TC", custom_data="Test data"
        )

        self.country = self.Country.objects.create(
            name="Test Country",
            slug="test-country",
            code="TC",
            code3="TST",
            population=1000000,
            phone="123",
            tld=".tc",
            capital="Test Capital",
            postal_code_format="",
            postal_code_regex="",
            continent=self.continent,
            custom_field="Test field",
        )

    def test_country_continent_relationship(self):
        """Test Country.continent FK with custom models"""
        self.assertIsNotNone(self.country.continent)
        self.assertEqual(self.country.continent.id, self.continent.id)
        self.assertEqual(self.country.continent.custom_data, "Test data")

        # Test reverse relationship
        countries = self.continent.countries.all()
        self.assertEqual(countries.count(), 1)
        self.assertEqual(countries.first().id, self.country.id)

    def test_city_country_relationship(self):
        """Test City.country FK with custom models"""
        city = self.City.objects.create(
            name="Test City",
            slug="1-test-city",
            name_std="Test City",
            location=Point(0, 0),
            population=100000,
            kind="PPLA",
            timezone="UTC",
            country=self.country,
            custom_population_verified=True,
        )

        self.assertIsNotNone(city.country)
        self.assertEqual(city.country.id, self.country.id)
        self.assertEqual(city.country.custom_field, "Test field")

        # Test reverse relationship
        cities = self.country.cities.all()
        self.assertEqual(cities.count(), 1)
        self.assertEqual(cities.first().id, city.id)

    def test_alternativename_relationship(self):
        """Test alt_names M2M with custom models - critical test for PR #203 / Issue #165"""
        # Load AlternativeName (which may or may not be swapped)
        AlternativeName = swapper.load_model("cities", "AlternativeName")

        # Create an alternative name
        alt_name = AlternativeName.objects.create(
            name="Test Alternative",
            language_code="en",
        )

        # Add alternative name to country
        self.country.alt_names.add(alt_name)

        # Verify relationship works
        self.assertEqual(self.country.alt_names.count(), 1)
        self.assertEqual(self.country.alt_names.first().name, "Test Alternative")

        # Verify we can query through the relationship
        countries_with_alt = self.Country.objects.filter(alt_names=alt_name)
        self.assertEqual(countries_with_alt.count(), 1)
        self.assertEqual(countries_with_alt.first().id, self.country.id)


@override_settings(
    CITIES_CONTINENT_MODEL="test_swappable_app.CustomContinent",
    CITIES_COUNTRY_MODEL="test_swappable_app.CustomCountry",
    CITIES_CITY_MODEL="test_swappable_app.CustomCity",
)
class CustomFieldPersistenceTest(TestCase):
    """Test that custom fields persist through updates"""

    def setUp(self):
        """Load swapped models"""
        self.Country = swapper.load_model("cities", "Country")

    def test_custom_fields_preserved_on_update(self):
        """Verify custom field data not lost on update"""
        country = self.Country.objects.create(
            name="Test Country",
            slug="test-country",
            code="TC",
            code3="TST",
            population=1000000,
            phone="123",
            tld=".tc",
            capital="Test Capital",
            postal_code_format="",
            postal_code_regex="",
            custom_field="Original value",
            is_verified=True,
        )

        # Update standard field
        country.population = 2000000
        country.save()

        # Reload from database
        country.refresh_from_db()

        # Verify custom fields still intact
        self.assertEqual(country.custom_field, "Original value")
        self.assertTrue(country.is_verified)
        self.assertEqual(country.population, 2000000)


class DefaultModelsTest(TestCase):
    """Test that default models are used when no swap is configured"""

    def test_default_continent_model(self):
        """Verify default Continent model used when not swapped"""
        # Note: This test runs without CITIES_CONTINENT_MODEL setting
        Continent = swapper.load_model("cities", "Continent")
        self.assertEqual(Continent.__name__, "Continent")
        self.assertEqual(Continent._meta.app_label, "cities")

    def test_default_country_model(self):
        """Verify default Country model used when not swapped"""
        Country = swapper.load_model("cities", "Country")
        self.assertEqual(Country.__name__, "Country")
        self.assertEqual(Country._meta.app_label, "cities")

    def test_default_city_model(self):
        """Verify default City model used when not swapped"""
        City = swapper.load_model("cities", "City")
        self.assertEqual(City.__name__, "City")
        self.assertEqual(City._meta.app_label, "cities")
