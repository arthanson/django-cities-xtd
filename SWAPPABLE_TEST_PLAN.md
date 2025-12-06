# Swappable Models Test Plan

## Overview
This document outlines the comprehensive test plan for django-cities swappable models functionality.

## Current Gap
- **Zero** test coverage for model swapping functionality
- No verification that custom models work correctly
- No testing of relationships between swapped models

## Proposed Test Structure

### 1. Test Application Setup

Create a test app with custom models:

```
test_project/test_swappable_app/
├── __init__.py
├── models.py           # Custom model implementations
├── settings.py         # Settings with CITIES_*_MODEL configured
└── tests/
    ├── __init__.py
    ├── test_custom_continent.py
    ├── test_custom_country.py
    ├── test_custom_city.py
    ├── test_custom_alternativename.py  # If/when implemented
    └── test_relationships.py
```

### 2. Custom Model Examples

#### test_swappable_app/models.py
```python
from django.db import models
from cities.models import (
    BaseContinent,
    BaseCountry,
    BaseCity,
)

class CustomContinent(BaseContinent):
    """Custom continent with extra field"""
    custom_data = models.TextField(blank=True)

    class Meta(BaseContinent.Meta):
        pass


class CustomCountry(BaseCountry):
    """Custom country with extra field"""
    custom_field = models.CharField(max_length=100, blank=True)

    class Meta(BaseCountry.Meta):
        pass


class CustomCity(BaseCity):
    """Custom city with extra fields"""
    custom_population_verified = models.BooleanField(default=False)

    class Meta(BaseCity.Meta):
        pass
```

### 3. Test Cases

#### A. Model Registration Tests
```python
class SwappableModelRegistrationTest(TestCase):
    """Test that swappable models are properly registered"""

    def test_continent_model_swapped(self):
        """Verify CITIES_CONTINENT_MODEL setting is respected"""

    def test_country_model_swapped(self):
        """Verify CITIES_COUNTRY_MODEL setting is respected"""

    def test_city_model_swapped(self):
        """Verify CITIES_CITY_MODEL setting is respected"""

    def test_default_models_when_not_swapped(self):
        """Verify default models used when no swap configured"""
```

#### B. Model Creation Tests
```python
class CustomModelCreationTest(TestCase):
    """Test creating instances of custom models"""

    def test_create_custom_continent(self):
        """Create instance of custom continent model"""

    def test_create_custom_country(self):
        """Create instance of custom country model"""

    def test_create_custom_city(self):
        """Create instance of custom city model"""

    def test_custom_fields_accessible(self):
        """Verify custom fields work correctly"""
```

#### C. Relationship Tests
```python
class SwappableModelRelationshipTest(TestCase):
    """Test relationships between swapped models"""

    def test_country_continent_relationship(self):
        """Test Country.continent FK with custom models"""

    def test_city_country_relationship(self):
        """Test City.country FK with custom models"""

    def test_city_region_relationship(self):
        """Test City.region FK (Region not swappable)"""

    def test_alternativename_relationship(self):
        """Test alt_names M2M with custom models"""
        # This is the critical test for PR #203 / Issue #165
```

#### D. Import Command Tests
```python
class ImportWithCustomModelsTest(TestCase):
    """Test data import with custom models"""

    def test_import_continents_custom_model(self):
        """Import continents into custom model"""

    def test_import_countries_custom_model(self):
        """Import countries into custom model"""

    def test_import_cities_custom_model(self):
        """Import cities into custom model"""

    def test_custom_fields_preserved_on_reimport(self):
        """Verify custom field data not lost on re-import"""
```

#### E. Manager Tests
```python
class CustomModelManagerTest(TestCase):
    """Test custom managers on swapped models"""

    def test_custom_manager_methods(self):
        """Test custom manager methods work"""

    def test_queryset_returns_custom_model(self):
        """Verify queries return custom model instances"""
```

#### F. Migration Tests
```python
class SwappableModelMigrationTest(TestCase):
    """Test migrations work with custom models"""

    def test_migrations_no_conflicts(self):
        """Verify no migration conflicts with custom models"""

    def test_migration_dependencies(self):
        """Test migration dependency resolution"""
```

### 4. AlternativeName Swappable Implementation Tests

**If/When AlternativeName becomes swappable:**

```python
class CustomAlternativeNameTest(TestCase):
    """Test custom AlternativeName model"""

    def test_custom_alternativename_model(self):
        """Test custom AlternativeName works"""

    def test_place_alt_names_relationship(self):
        """Test Place.alt_names M2M with custom AlternativeName"""

    def test_import_alternative_names(self):
        """Test importing alternative names into custom model"""
```

### 5. Edge Cases & Error Handling

```python
class SwappableModelEdgeCaseTest(TestCase):
    """Test edge cases and error conditions"""

    def test_invalid_model_path(self):
        """Test error handling for invalid CITIES_*_MODEL path"""

    def test_missing_base_class(self):
        """Test error when custom model doesn't inherit base"""

    def test_missing_meta_class(self):
        """Test custom model without Meta class"""

    def test_circular_import_prevention(self):
        """Test no circular import issues"""
```

## Implementation Priority

### High Priority (Immediate)
1. **Relationship tests** - Verify current swappable models work correctly
2. **Import command tests** - Ensure data import works with custom models
3. **AlternativeName reference test** - Specifically test the PR #203 issue

### Medium Priority
1. **Migration tests** - Ensure migrations work smoothly
2. **Custom manager tests** - Verify manager functionality
3. **Edge case tests** - Error handling and validation

### Low Priority (Nice to Have)
1. **Performance tests** - Compare performance with/without swapping
2. **Documentation tests** - Ensure examples in README work

## Test Execution Strategy

### Separate Test Database
- Use separate settings file for swappable tests
- Configure CITIES_*_MODEL settings
- Use different database or schema

### Test Isolation
- Each test should be independent
- Use transactions or TestCase tearDown
- Clean up test data properly

### CI/CD Integration
- Add swappable model tests to CI pipeline
- Test against multiple Django versions
- Test with/without custom models

## Success Criteria

- ✅ All swappable models (Continent, Country, City) have test coverage
- ✅ Relationship between swapped and non-swapped models tested
- ✅ Import commands work with custom models
- ✅ AlternativeName reference issue (PR #203) is tested
- ✅ Documentation examples are validated by tests
- ✅ All tests pass on supported Django versions

## Notes

- Current test suite has **zero** swappable model tests
- PR #203 attempted to fix AlternativeName swapping but needs validation
- Issue #165 reports specific failures that need test coverage
- Tests should catch regressions in swappable model functionality
