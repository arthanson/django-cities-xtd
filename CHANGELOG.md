# Changelog #

## v0.7.0 ##

### Added ###

- Added Django 6.0 compatibility
- Added Docker-based testing infrastructure with support for multiple Python and Django versions
- Added MySQL testing support
- Added swappable models support for Country model
- Added comprehensive refactoring of importer system with modular architecture
- Added new services: downloader, parser, validator, and index_builder
- Added BigAutoField migration for Django 3.2+ compatibility
- Added pre-commit hooks configuration
- Added improved postal code import handling
- Added constants extraction for better code organization

### Changed ###

- Major performance improvements and refactoring
- Refactored importer into separate modules (alt_name, base, city, country, district, postal_code, region, subregion)
- Improved file download optimization
- Updated to use pyproject.toml for build configuration
- Updated code formatting with ruff
- Improved unicode string ordering
- Enhanced documentation

### Removed ###

- Removed support for Django 1.x, 2.x, 3.x and very old versions of Python
- Removed Python 2 support (already removed in v0.6)
- Removed Python 3.3-3.5 support (already removed in v0.6)
- Removed Travis CI configuration (replaced with Docker-based testing)

## v0.6.2 ##

- Fix Django missing migration, thanks @RafaPinzon93
- Updated Python version classifiers, thanks @leogregianin

## v0.6.1 ##

### Added ###

- Added support for Django 4.0

## v0.6 ##

### Added ###

- Added `filter_horizontal` to neighbours field in Country model
- Added support for Django 3.0

### Changed ###

- Improved the neighbours admin page
- Updated Travis test matrix and supported/compatibility table in README
- Linting fixups and added Travis check for linting
- Updated Travis config to run on Xenial

### Removed ###

- Python 2 support
- Python 3.3-3.5 support and testing
- Django 1.7-1.10
- Django 2.0-2.1

## v0.5.0.6 ##

- Bug fixes and maintenance release

## v0.5.0.5 ##

- Bug fixes and maintenance release

## v0.5.0.4 ##

- Bug fixes and maintenance release

## v0.5.0.3 ##

- Bug fixes and improvements

## v0.5.0.2 ##

- Bug fixes and maintenance release

## v0.5.0.1 ##

- Bug fixes and maintenance release

## v0.5 ##

- Initial release with major feature additions

## v0.4.2 ##

- Bug fixes and improvements

## v0.4.1 ##

- Use Django's native migrations
- Last version before detailed changelog tracking

## Previous versions ##

### Changed
- Added ``cities.plugin.reset_queries.Plugin`` that calls reset_queries randomly (default chance is 0.000002 per imported city or district). See CITIES_PLUGINS in Configuration example for details
- It's now possible to specify several files to be downloaded and processed. See Configuration example for details.
