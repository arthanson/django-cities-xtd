"""City importer"""

from django.db import transaction
from django.db.models import Q
from swapper import load_model

from ..conf import city_types
from ..exceptions import ValidationError
from ..models import Subregion
from .base import BaseImporter

City = load_model("cities", "City")


class CityImporter(BaseImporter):
    """Imports city data from GeoNames"""

    def get_file_key(self):
        return "city"

    def get_model_class(self):
        return City

    def get_description(self):
        return "Importing cities"

    def build_indices(self):
        """Build country and region indices"""
        self.country_index = self.index_builder.build_country_index(self.options.get("quiet"))
        self.region_index = self.index_builder.build_region_index(self.options.get("quiet"))

    def parse_item(self, item):
        """Parse city data"""
        # Filter by feature code - only import city types
        if item.get("featureCode") not in city_types:
            return None

        # Validate geonameid
        city_id = self.validator.parse_int(item.get("geonameid"), "geonameid", entity_type="City")

        # Parse location
        location = self.validator.parse_location(item.get("latitude"), item.get("longitude"), entity_type="City")

        defaults = {
            "name": item["name"],
            "kind": item["featureCode"],
            "name_std": item.get("asciiName", ""),
            "location": location,
            "population": self.validator.parse_int(item.get("population"), "population", default=0),
            "timezone": item.get("timezone", ""),
        }

        # Parse optional elevation
        try:
            defaults["elevation"] = self.validator.parse_int(item.get("elevation"), "elevation")
        except ValidationError:
            defaults["elevation"] = None

        # Look up country
        country_code = item.get("countryCode")
        try:
            defaults["country"] = self.validator.lookup_foreign_key(
                self.country_index, country_code, "Country", entity_type="City"
            )
        except ValidationError:
            raise

        # Look up region
        region_code = item.get("admin1Code", "")
        region_key = country_code + "." + region_code
        try:
            defaults["region"] = self.validator.lookup_foreign_key(
                self.region_index, region_key, "Region", entity_type="City"
            )
        except ValidationError:
            # Import at runtime to respect test-time setting overrides
            from ..conf import SKIP_CITIES_WITH_EMPTY_REGIONS

            self.logger.debug(
                "SKIP_CITIES_WITH_EMPTY_REGIONS: %s",
                str(SKIP_CITIES_WITH_EMPTY_REGIONS),
            )
            if SKIP_CITIES_WITH_EMPTY_REGIONS:
                self.logger.debug(
                    "%s: %s: Cannot find region: '%s' -- skipping",
                    country_code,
                    item["name"],
                    region_code,
                )
                return None  # Skip this city
            else:
                defaults["region"] = None

        # Look up subregion (with fallback queries)
        subregion_code = item.get("admin2Code")
        defaults["subregion"] = self._lookup_subregion(
            country_code, region_code, subregion_code, defaults.get("region"), item["name"]
        )

        return {"id": city_id, "defaults": defaults}

    def _lookup_subregion(self, country_code, region_code, subregion_code, region, city_name):
        """
        Look up subregion with fallback logic

        Args:
            country_code: Country code
            region_code: Region code
            subregion_code: Subregion code
            region: Region object
            city_name: City name (for logging)

        Returns:
            Subregion object or None
        """
        if not subregion_code:
            return None

        # Try region_index first
        subregion_key = f"{country_code}.{region_code}.{subregion_code}"
        try:
            return self.region_index[subregion_key]
        except KeyError:
            pass

        # Fallback: Try database lookup by name
        if region:
            try:
                with transaction.atomic():
                    return Subregion.objects.get(
                        Q(name=subregion_code) | Q(name=subregion_code.replace(" (undefined)", "")),
                        region=region,
                    )
            except Subregion.DoesNotExist:
                pass

            # Fallback: Try database lookup by name_std
            try:
                with transaction.atomic():
                    return Subregion.objects.get(
                        Q(name_std=subregion_code) | Q(name_std=subregion_code.replace(" (undefined)", "")),
                        region=region,
                    )
            except Subregion.DoesNotExist:
                pass

        # Not found
        if subregion_code:
            self.logger.debug(
                "%s: %s: Cannot find subregion: '%s'",
                country_code,
                city_name,
                subregion_code,
            )

        return None

    def create_or_update(self, parsed_data):
        """Create or update city record"""
        city_id = parsed_data["id"]
        defaults = parsed_data["defaults"]

        return City.objects.update_or_create(id=city_id, defaults=defaults)
