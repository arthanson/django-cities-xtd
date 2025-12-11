"""Country importer"""

from django.db.models import CharField, ForeignKey
from swapper import load_model
from tqdm import tqdm

from ..conf import CURRENCY_SYMBOLS, NO_LONGER_EXISTENT_COUNTRY_CODES
from .base import BaseImporter

Country = load_model("cities", "Country")


class CountryImporter(BaseImporter):
    """Imports country data from GeoNames"""

    def __init__(self, command, options):
        super().__init__(command, options)
        self.neighbours_map = {}  # {country: [neighbour_codes]}
        self.countries_map = {}  # {code: country}
        self.import_continents_as_fks = False

    def get_file_key(self):
        return "country"

    def get_model_class(self):
        return Country

    def get_description(self):
        return "Importing countries"

    def build_indices(self):
        """Build continent index"""
        self.continent_index = self.index_builder.build_continent_index(self.options.get("quiet"))

        # Check if continent is a ForeignKey or CharField
        self.import_continents_as_fks = type(Country._meta.get_field("continent")) is ForeignKey

    def load_data(self):
        """Load country data, filtering out obsolete country codes"""
        all_data = list(self.parser.get_data(self.get_file_key()))
        # Filter out NO_LONGER_EXISTENT_COUNTRY_CODES
        return [d for d in all_data if d["code"] not in NO_LONGER_EXISTENT_COUNTRY_CODES]

    def parse_item(self, item):
        """Parse country data"""
        # Validate geonameid
        country_id = self.validator.parse_int(item.get("geonameid"), "geonameid", entity_type="Country")

        # Parse area
        area = None
        if item.get("area"):
            try:
                area = int(float(item["area"]))
            except (ValueError, TypeError):
                pass

        # Build defaults dict
        defaults = {
            "name": item["name"],
            "code": item["code"],
            "code3": item["code3"],
            "population": item["population"],
            "continent": (
                self.continent_index[item["continent"]] if self.import_continents_as_fks else item["continent"]
            ),
            "tld": item["tld"][1:] if item.get("tld") else "",  # strip the leading .
            "phone": item["phone"],
            "currency": item.get("currencyCode", ""),
            "currency_name": item.get("currencyName", ""),
            "capital": item.get("capital", ""),
            "area": area,
        }

        # Handle language_codes vs languages field (model variations)
        if hasattr(Country, "language_codes"):
            defaults["language_codes"] = item.get("languages", "")
        elif hasattr(Country, "languages") and type(getattr(Country, "languages")) is CharField:
            defaults["languages"] = item.get("languages", "")

        # These fields shouldn't impact saving older models (that don't have these attributes)
        try:
            defaults["currency_symbol"] = CURRENCY_SYMBOLS.get(item.get("currencyCode"), None)
            defaults["postal_code_format"] = item.get("postalCodeFormat", "")
            defaults["postal_code_regex"] = item.get("postalCodeRegex", "")
        except AttributeError:
            pass

        # Store for later processing
        return {
            "id": country_id,
            "defaults": defaults,
            "neighbours": item.get("neighbours", "").split(","),
        }

    def create_or_update(self, parsed_data):
        """Create or update country record"""
        country_id = parsed_data["id"]
        defaults = parsed_data["defaults"]
        neighbour_codes = parsed_data["neighbours"]

        # Make importing countries idempotent
        country, created = Country.objects.update_or_create(id=country_id, defaults=defaults)

        # Store for neighbours processing
        self.neighbours_map[country] = neighbour_codes
        self.countries_map[country.code] = country

        return country, created

    def cleanup(self):
        """Process country neighbours after all countries are imported"""
        if not self.neighbours_map:
            return

        for country, neighbour_codes in tqdm(
            list(self.neighbours_map.items()),
            disable=self.options.get("quiet"),
            total=len(self.neighbours_map),
            desc="Importing country neighbours",
        ):
            # Filter out invalid codes and get country objects
            neighbours = [x for x in [self.countries_map.get(code) for code in neighbour_codes if code] if x]
            country.neighbours.add(*neighbours)
