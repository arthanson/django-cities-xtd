# Release Notes

> **Note**: For a complete changelog of all versions, see [CHANGELOG.md](../../CHANGELOG.md) in the project root.

## 0.7.0

**Major Release: Refactoring, Performance Improvements, and Django 6 Compatibility**

This release includes significant refactoring, performance improvements, and adds support for Django 6.0.

### Major Changes

- **Django 6.0 Compatibility**: Full support for Django 6.0
- **Performance Improvements**: Major refactoring of the importer system for better performance
- **Modular Architecture**: Importer system refactored into separate modules for better maintainability
- **Docker Testing**: Added comprehensive Docker-based testing infrastructure
- **MySQL Support**: Added MySQL testing support
- **Swappable Models**: Added support for swappable Country model
- **BigAutoField Migration**: Added migration for Django 3.2+ BigAutoField support

### Breaking Changes

- Removed support for Django 1.x, 2.x, and 3.x
- Removed support for very old Python versions
- Requires Python 3.12+ and Django 5.0+

### Upgrading

When upgrading to 0.7.0, ensure you:
1. Are using Python 3.12+ and Django 5.0+
2. Run migrations: `python manage.py migrate cities`
3. Review any custom importer code as the importer architecture has changed

## 0.6.2

- Fix Django missing migration
- Updated Python version classifiers

## 0.6.1

- Added support for Django 4.0

## 0.6

**Breaking Changes**

- Removed Python 2 support
- Removed Python 3.3-3.5 support
- Removed Django 1.7-1.10 support
- Removed Django 2.0-2.1 support

### New Features

- Added `filter_horizontal` to neighbours field in Country model
- Added support for Django 3.0

### Improvements

- Improved the neighbours admin page
- Updated test matrix and compatibility table
- Linting improvements

## 0.5.0.6

- Bug fixes and maintenance release

## 0.5.0.5

- Bug fixes and maintenance release

## 0.5.0.4

- Bug fixes and maintenance release

## 0.5.0.3

- Bug fixes and improvements

## 0.5.0.2

- Bug fixes and maintenance release

## 0.5.0.1

- Bug fixes and maintenance release

## 0.5

- Initial release with major feature additions

## 0.4.2

- Bug fixes and improvements

## 0.4.1

Use Django's native migrations

### Upgrading from 0.4.1

Upgrading from 0.4.1 is likely to cause problems trying to apply a migration when the tables already exist. In this case a fake migration needs to be applied:

```bash
python manage.py migrate cities 0001 --fake
```

## 0.4

** **This release of django-cities is not backwards compatible with previous versions** **

The country model has some new fields:
 - elevation
 - area
 - currency
 - currency_name
 - languages
 - neighbours
 - capital
 - phone

Alternative name support has been completely overhauled. The code and usage should now be much simpler. See the updated examples below.

The code field no longer contains the parent code. Eg. the code for California, US is now "CA". In the previous release it was "US.CA".

These changes mean that upgrading from a previous version isn't simple. All of the place IDs are the same though, so if you do want to upgrade it should be possible.
