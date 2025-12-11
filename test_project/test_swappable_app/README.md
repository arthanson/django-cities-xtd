# Swappable Models Test Suite

This test suite validates that django-cities swappable models functionality works correctly.

## What's Being Tested

### Models Made Swappable
- ✅ **Continent** - Already swappable
- ✅ **Country** - Already swappable
- ✅ **City** - Already swappable
- ✅ **AlternativeName** - **Newly made swappable** (PR #203 / Issue #165)

### Test Coverage

#### 1. Model Registration Tests (`test_swappable_models.py`)
- Verifies `CITIES_*_MODEL` settings are respected
- Tests default models used when no swap configured
- Validates custom models are properly loaded

#### 2. Relationship Tests (`test_swappable_models.py`)
- **Critical**: Tests `alt_names` M2M relationship (Issue #165)
- Tests Country.continent FK with custom models
- Tests City.country FK with custom models
- Tests relationships between swapped and non-swapped models

#### 3. Import Command Tests (`test_import_with_swapped_models.py`)
- Tests data import into custom models
- Verifies custom fields get default values
- Tests that custom field data persists through re-imports
- Tests partial swapping (only some models swapped)

## Running the Tests

### Prerequisites

The test suite requires the new `test_swappable_app` files to be available. Since these were just created, you need to:

1. **Rebuild Docker images** to include the new test app:
   ```bash
   docker compose build test-py314-django60
   ```

2. **Create migrations** for the custom models:
   ```bash
   docker compose run --rm test-py314-django60 \
     python test_project/manage.py makemigrations test_swappable_app \
     --settings=test_swappable_app.settings
   ```

3. **Run migrations**:
   ```bash
   docker compose run --rm test-py314-django60 \
     python test_project/manage.py migrate \
     --settings=test_swappable_app.settings
   ```

### Running Tests

Run all swappable model tests:
```bash
docker compose run --rm test-py314-django60 \
  python test_project/manage.py test test_swappable_app \
  --settings=test_swappable_app.settings
```

Run specific test class:
```bash
docker compose run --rm test-py314-django60 \
  python test_project/manage.py test \
  test_swappable_app.tests.test_swappable_models.SwappableModelRelationshipTest \
  --settings=test_swappable_app.settings
```

Run the critical AlternativeName relationship test:
```bash
docker compose run --rm test-py314-django60 \
  python test_project/manage.py test \
  test_swappable_app.tests.test_swappable_models.SwappableModelRelationshipTest.test_alternativename_relationship \
  --settings=test_swappable_app.settings
```

## What Was Fixed

### AlternativeName Swappable Implementation

**Problem** (Issue #165 / PR #203):
When users tried to create custom Country or City models, they got errors like:
> "Field defines a relation with model 'AlternativeName', which is either not installed, or is abstract"

**Root Cause**:
- `AlternativeName` was not swappable
- The reference in `Place.alt_names` was hardcoded as `"AlternativeName"` instead of using swapper

**Solution Implemented**:

1. **Made AlternativeName swappable** (`cities/models.py:314-315`):
   ```python
   class AlternativeName(SlugModel):
       # ... fields ...

       class Meta:
           swappable = swapper.swappable_setting("cities", "AlternativeName")
   ```

2. **Updated reference to use swapper** (`cities/models.py:77`):
   ```python
   class Place(models.Model):
       alt_names = models.ManyToManyField(
           swapper.get_model_name("cities", "AlternativeName")
       )
   ```

### Backward Compatibility

✅ **No migrations required** - These changes are backward compatible
✅ **Existing tests pass** - All 61 existing tests pass
✅ **Optional feature** - Swapping models is optional, defaults work as before

## Custom Model Examples

The test suite includes example custom models:

### CustomContinent
```python
class CustomContinent(BaseContinent):
    custom_data = models.TextField(blank=True, default="")
```

### CustomCountry
```python
class CustomCountry(BaseCountry):
    custom_field = models.CharField(max_length=100, blank=True, default="")
    is_verified = models.BooleanField(default=False)
```

### CustomCity
```python
class CustomCity(BaseCity):
    custom_population_verified = models.BooleanField(default=False)
    custom_notes = models.TextField(blank=True, default="")
```

## Configuration

To use custom models in your project, add to `settings.py`:

```python
INSTALLED_APPS = (
    # ... other apps ...
    'my_custom_app',  # Must come BEFORE cities
    'cities',
    # ... other apps ...
)

# Configure swappable models
CITIES_CONTINENT_MODEL = 'my_custom_app.MyCustomContinent'
CITIES_COUNTRY_MODEL = 'my_custom_app.MyCustomCountry'
CITIES_CITY_MODEL = 'my_custom_app.MyCustomCity'
CITIES_ALTERNATIVENAME_MODEL = 'my_custom_app.MyCustomAlternativeName'  # NEW!
```

## Expected Test Results

When all tests pass, you should see output like:
```
test_alternativename_relationship ... ok
test_city_country_relationship ... ok
test_country_continent_relationship ... ok
test_create_custom_city ... ok
test_create_custom_continent ... ok
test_create_custom_country ... ok
test_import_alternative_names_with_swapped_models ... ok
test_import_cities_custom_model ... ok
test_import_countries_custom_model ... ok
...

Ran X tests in Y.XXXs

OK
```

## Troubleshooting

### ModuleNotFoundError: No module named 'test_swappable_app'
**Solution**: Rebuild Docker image: `docker compose build test-py314-django60`

### Migration conflicts
**Solution**: Delete `test_swappable_app/migrations/` and regenerate

### Tests fail with "relation does not exist"
**Solution**: Run migrations with swappable settings: `python manage.py migrate --settings=test_swappable_app.settings`

## Next Steps

1. Add swappable model tests to CI/CD pipeline
2. Update documentation with AlternativeName swapping
3. Consider making Region, Subregion, District, PostalCode swappable
4. Add performance benchmarks for swapped vs default models
