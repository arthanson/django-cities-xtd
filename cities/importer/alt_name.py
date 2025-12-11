"""Alternative name importer"""

from swapper import load_model

from ..conf import INCLUDE_AIRPORT_CODES, INCLUDE_NUMERIC_ALTERNATIVE_NAMES, settings
from ..models import AlternativeName, PostalCode, Region, Subregion
from .base import BaseImporter

City = load_model("cities", "City")


class AlternativeNameImporter(BaseImporter):
    """Imports alternative name data from GeoNames"""

    def get_file_key(self):
        return "alt_name"

    def get_model_class(self):
        return AlternativeName

    def get_description(self):
        return "Importing data for alternative names"

    def build_indices(self):
        """Build comprehensive geo index"""
        self.geo_index = self.index_builder.build_geo_index(self.options.get("quiet"))

    def parse_item(self, item):
        """Parse alternative name data"""
        # Get locale (language code)
        locale = item.get("language", "")
        if not locale:
            locale = "und"

        # Filter by configured locales
        if locale not in settings.locales and "all" not in settings.locales:
            self.logger.debug(
                "Alternative name with language [%s]: %s (%s) -- skipping",
                item.get("language"),
                item.get("name"),
                item.get("nameid"),
            )
            return None

        # Check if geo id exists in index
        geo_id = self.validator.parse_int(item.get("geonameid"), "geonameid", entity_type="AlternativeName")

        try:
            geo_info = self.geo_index[geo_id]
        except KeyError:
            # Unknown geonameid, skip
            return None

        # Get alternative name ID
        alt_id = self.validator.parse_int(item.get("nameid"), "nameid", entity_type="AlternativeName")

        # Check for numeric names (skip if configured)
        name = item.get("name", "")
        try:
            int(name)
            is_numeric = True
        except ValueError:
            is_numeric = False

        if is_numeric and not INCLUDE_NUMERIC_ALTERNATIVE_NAMES:
            self.logger.debug(
                "Trying to add a numeric alternative name to %s (%s): %s -- skipping",
                geo_info["object"].name,
                geo_info["type"].__name__,
                name,
            )
            return None

        # Handle special "post" locale - creates postal codes instead of alt names
        if locale == "post":
            self._create_postal_code_from_alt_name(geo_info, name)
            return None

        return {
            "alt_id": alt_id,
            "name": name,
            "locale": locale,
            "is_preferred": self.validator.parse_bool(item.get("isPreferred", "")),
            "is_short": self.validator.parse_bool(item.get("isShort", "")),
            "is_historic": self._parse_historic(item.get("isHistoric", ""), locale),
            "geo_info": geo_info,
            "item": item,  # Keep original for hooks
        }

    def _parse_historic(self, is_historic_value, locale):
        """Parse is_historic field"""
        if locale == "fr_1793":
            return True
        if is_historic_value and is_historic_value != "\n":
            return True
        return False

    def _create_postal_code_from_alt_name(self, geo_info, name):
        """Create postal code from alternative name with locale='post'"""
        try:
            geo_type = geo_info["type"]
            geo_obj = geo_info["object"]

            if geo_type == Region:
                PostalCode.objects.get_or_create(
                    code=name,
                    country=geo_obj.country,
                    region=geo_obj,
                    region_name=geo_obj.name,
                )
            elif geo_type == Subregion:
                PostalCode.objects.get_or_create(
                    code=name,
                    country=geo_obj.region.country,
                    region=geo_obj.region,
                    subregion=geo_obj,
                    region_name=geo_obj.region.name,
                    subregion_name=geo_obj.name,
                )
            elif geo_type == City:
                region_name = geo_obj.region.name if geo_obj.region else ""
                subregion_name = geo_obj.subregion.name if geo_obj.subregion else ""
                PostalCode.objects.get_or_create(
                    code=name,
                    country=geo_obj.country,
                    region=geo_obj.region,
                    subregion=geo_obj.subregion,
                    region_name=region_name,
                    subregion_name=subregion_name,
                )
        except KeyError:
            pass

    def create_or_update(self, parsed_data):
        """Create or update alternative name record"""
        alt_id = parsed_data["alt_id"]
        name = parsed_data["name"]
        locale = parsed_data["locale"]
        is_preferred = parsed_data["is_preferred"]
        is_short = parsed_data["is_short"]
        is_historic = parsed_data["is_historic"]
        geo_info = parsed_data["geo_info"]

        # Get or create alternative name
        try:
            alt = AlternativeName.objects.get(id=alt_id)
            created = False
        except AlternativeName.DoesNotExist:
            alt = AlternativeName(id=alt_id)
            created = True

        # Set fields
        alt.name = name
        alt.is_preferred = is_preferred
        alt.is_short = is_short
        alt.is_historic = is_historic

        # Set language_code or language (depending on model)
        try:
            alt.language_code = locale
        except AttributeError:
            alt.language = locale

        # Set kind field if it exists
        if hasattr(alt, "kind"):
            if locale in ("abbr", "link", "name") or (INCLUDE_AIRPORT_CODES and locale in ("iana", "icao", "faac")):
                alt.kind = locale
            elif locale not in settings.locales and "all" not in settings.locales:
                self.logger.debug("Unknown alternative name type: %s -- skipping", locale)
                return None, False

        # Save and link to geographic object
        alt.save()
        geo_info["object"].alt_names.add(alt)

        return alt, created

    def log_result(self, obj, created):
        """Log import result"""
        locale = obj.language_code if hasattr(obj, "language_code") else obj.language
        self.logger.debug("Added alt name: %s, %s", locale, obj)
