"""Region importer"""

import json
import os

from ..exceptions import ValidationError
from ..models import Region
from .base import BaseImporter


class RegionImporter(BaseImporter):
    """Imports region data from GeoNames"""

    def __init__(self, command, options):
        super().__init__(command, options)
        self.countries_not_found = {}

    def get_file_key(self):
        return "region"

    def get_model_class(self):
        return Region

    def get_description(self):
        return "Importing regions"

    def build_indices(self):
        """Build country index"""
        self.country_index = self.index_builder.build_country_index(self.options.get("quiet"))

    def parse_item(self, item):
        """Parse region data"""
        # Validate geonameid
        region_id = self.validator.parse_int(item.get("geonameid"), "geonameid", entity_type="Region")

        # Split code into country and region codes
        try:
            country_code, region_code = item["code"].split(".")
        except (KeyError, ValueError):
            raise ValidationError(f"Region: Invalid code format: {item.get('code')}")

        defaults = {
            "name": item["name"],
            "name_std": item.get("asciiName", ""),
            "code": region_code,
        }

        # Look up country
        try:
            defaults["country"] = self.validator.lookup_foreign_key(
                self.country_index, country_code, "Country", entity_type="Region"
            )
        except ValidationError:
            # Track countries not found for reporting
            self.countries_not_found.setdefault(country_code, []).append(defaults["name"])
            raise

        return {"id": region_id, "defaults": defaults}

    def create_or_update(self, parsed_data):
        """Create or update region record"""
        region_id = parsed_data["id"]
        defaults = parsed_data["defaults"]

        return Region.objects.update_or_create(id=region_id, defaults=defaults)

    def cleanup(self):
        """Write countries_not_found report if any"""
        if not self.countries_not_found:
            return

        countries_not_found_file = os.path.join(self.command.data_dir, "countries_not_found.json")
        try:
            with open(countries_not_found_file, "w+") as fp:
                json.dump(self.countries_not_found, fp)
            self.logger.info("Wrote countries not found report to: %s", countries_not_found_file)
        except Exception as e:
            self.logger.warning("Unable to write log file '%s': %s", countries_not_found_file, e)
