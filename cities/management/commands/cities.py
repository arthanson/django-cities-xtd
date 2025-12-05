"""
GeoNames city data import script.
Requires the following files:

http://download.geonames.org/export/dump/
- Countries:            countryInfo.txt
- Regions:              admin1CodesASCII.txt
- Subregions:           admin2Codes.txt
- Cities:               cities5000.zip
- Districts:            hierarchy.zip
- Localization:         alternateNames.zip

http://download.geonames.org/export/zip/
- Postal Codes:         allCountries.zip
"""

import logging
import os

from django.core.management.base import BaseCommand
from django.db import transaction
from swapper import load_model
from tqdm import tqdm

from ...conf import HookException, import_opts, import_opts_all, settings
from ...importer import (
    AlternativeNameImporter,
    CityImporter,
    CountryImporter,
    DistrictImporter,
    PostalCodeImporter,
    RegionImporter,
    SubregionImporter,
)
from ...models import District, PostalCode, Region, Subregion

# Load swappable models
Continent = load_model("cities", "Continent")
Country = load_model("cities", "Country")
City = load_model("cities", "City")

# Only log errors during Travis tests
LOGGER_NAME = os.environ.get("TRAVIS_LOGGER_NAME", "cities")


class Command(BaseCommand):
    """
    Django management command for importing GeoNames data

    Delegates to specialized importer classes for each entity type.
    """

    # Map import types to importer classes
    IMPORTERS = {
        "country": CountryImporter,
        "region": RegionImporter,
        "subregion": SubregionImporter,
        "city": CityImporter,
        "district": DistrictImporter,
        "postal_code": PostalCodeImporter,
        "alt_name": AlternativeNameImporter,
    }

    if hasattr(settings, "data_dir"):
        data_dir = settings.data_dir
    else:
        app_dir = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + "/../..")
        data_dir = os.path.join(app_dir, "data")

    logger = logging.getLogger(LOGGER_NAME)

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            dest="force",
            help="Import even if files are up-to-date.",
        )
        parser.add_argument(
            "--import",
            metavar="DATA_TYPES",
            default="all",
            dest="import",
            help="Selectively import data. Comma separated list of data types: " + str(import_opts).replace("'", ""),
        )
        parser.add_argument(
            "--flush",
            metavar="DATA_TYPES",
            default="",
            dest="flush",
            help="Selectively flush data. Comma separated list of data types.",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            default=False,
            dest="quiet",
            help="Do not show the progress bar.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        """Main entry point for command"""
        self.options = options

        # Handle flush operations
        self.flushes = [e for e in self.options.get("flush", "").split(",") if e]
        if "all" in self.flushes:
            self.flushes = import_opts_all

        for flush in self.flushes:
            flush_func = getattr(self, "flush_" + flush)
            flush_func()

        # Handle import operations
        self.imports = [e for e in self.options.get("import", "").split(",") if e]
        if "all" in self.imports:
            self.imports = import_opts_all

        # Don't import if we're only flushing
        if self.flushes:
            self.imports = []

        for import_type in self.imports:
            self._run_importer(import_type)

    def _run_importer(self, import_type):
        """
        Run the appropriate importer for the given import type

        Args:
            import_type: Type of data to import (e.g., 'country', 'city')
        """
        try:
            importer_class = self.IMPORTERS[import_type]
        except KeyError:
            self.logger.error("Unknown import type: %s", import_type)
            return

        importer = importer_class(self, self.options)
        importer.run()

    def call_hook(self, hook, *args, **kwargs):
        """
        Call plugin hooks (for backward compatibility)

        Args:
            hook: Hook name
            *args: Arguments to pass to hook
            **kwargs: Keyword arguments to pass to hook

        Returns:
            bool: True if should continue, False if should skip
        """
        if hasattr(settings, "plugins"):
            for plugin in settings.plugins.get(hook, []):
                try:
                    func = getattr(plugin, hook)
                    func(self, *args, **kwargs)
                except HookException as e:
                    error = str(e)
                    if error:
                        self.logger.error(error)
                    return False
        return True

    # Flush methods

    def flush_country(self):
        """Delete all country data"""
        self.logger.info("Flushing country data")
        Country.objects.all().delete()

    def flush_region(self):
        """Delete all region data"""
        self.logger.info("Flushing region data")
        Region.objects.all().delete()

    def flush_subregion(self):
        """Delete all subregion data"""
        self.logger.info("Flushing subregion data")
        Subregion.objects.all().delete()

    def flush_city(self):
        """Delete all city data"""
        self.logger.info("Flushing city data")
        City.objects.all().delete()

    def flush_district(self):
        """Delete all district data"""
        self.logger.info("Flushing district data")
        District.objects.all().delete()

    def flush_postal_code(self):
        """Delete all postal code data"""
        self.logger.info("Flushing postal code data")
        PostalCode.objects.all().delete()

    def flush_alt_name(self):
        """Delete all alternative name data"""
        self.logger.info("Flushing alternate name data")
        for type_ in (Country, Region, Subregion, City, District, PostalCode):
            plural_type_name = type_.__name__ if type_.__name__[-1] != "y" else "{}ies".format(type_.__name__[:-1])
            for obj in tqdm(
                type_.objects.all(),
                disable=self.options.get("quiet"),
                total=type_.objects.count(),
                desc="Flushing alternative names for {}".format(plural_type_name),
            ):
                obj.alt_names.all().delete()
