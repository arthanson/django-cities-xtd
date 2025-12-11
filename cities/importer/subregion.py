"""Subregion importer"""

import json
import os

from ..exceptions import ValidationError
from ..models import Subregion
from .base import BaseImporter


class SubregionImporter(BaseImporter):
    """Imports subregion data from GeoNames"""

    def __init__(self, command, options):
        super().__init__(command, options)
        self.regions_not_found = {}

    def get_file_key(self):
        return "subregion"

    def get_model_class(self):
        return Subregion

    def get_description(self):
        return "Importing subregions"

    def build_indices(self):
        """Build country and region indices"""
        self.country_index = self.index_builder.build_country_index(self.options.get("quiet"))
        self.region_index = self.index_builder.build_region_index(self.options.get("quiet"))

    def parse_item(self, item):
        """Parse subregion data"""
        # Validate geonameid
        subregion_id = self.validator.parse_int(item.get("geonameid"), "geonameid", entity_type="Subregion")

        # Split code into country, region, and subregion codes
        try:
            country_code, region_code, subregion_code = item["code"].split(".")
        except (KeyError, ValueError):
            raise ValidationError(f"Subregion: Invalid code format: {item.get('code')}")

        defaults = {
            "name": item["name"],
            "name_std": item.get("asciiName", ""),
            "code": subregion_code,
        }

        # Look up region
        region_key = country_code + "." + region_code
        try:
            defaults["region"] = self.validator.lookup_foreign_key(
                self.region_index, region_key, "Region", entity_type="Subregion"
            )
        except ValidationError:
            # Track regions not found for reporting
            self.regions_not_found.setdefault(country_code, {})
            self.regions_not_found[country_code].setdefault(region_code, []).append(defaults["name"])
            self.logger.debug("Subregion: %s %s: Cannot find region", item["code"], defaults["name"])
            raise

        return {"id": subregion_id, "defaults": defaults}

    def create_or_update(self, parsed_data):
        """Create or update subregion record"""
        subregion_id = parsed_data["id"]
        defaults = parsed_data["defaults"]

        return Subregion.objects.update_or_create(id=subregion_id, defaults=defaults)

    def cleanup(self):
        """Write regions_not_found report and free memory"""
        # Write report if any regions not found
        if self.regions_not_found:
            regions_not_found_file = os.path.join(self.command.data_dir, "regions_not_found.json")
            try:
                with open(regions_not_found_file, "w+") as fp:
                    json.dump(self.regions_not_found, fp)
                self.logger.info("Wrote regions not found report to: %s", regions_not_found_file)
            except Exception as e:
                self.logger.warning("Unable to write log file '%s': %s", regions_not_found_file, e)

        # Delete region_index to free memory
        del self.region_index
