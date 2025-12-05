"""District importer"""

from django.contrib.gis.gdal.envelope import Envelope
from django.contrib.gis.measure import D
from django.db import transaction
from swapper import load_model

from ..conf import district_types
from ..exceptions import ValidationError
from ..models import District
from ..util import geo_distance
from .base import BaseImporter

try:
    from django.contrib.gis.db.models.functions import Distance
except ImportError:
    Distance = None

City = load_model("cities", "City")


class DistrictImporter(BaseImporter):
    """Imports district data from GeoNames"""

    def get_file_key(self):
        return "city"

    def get_model_class(self):
        return District

    def get_description(self):
        return "Importing districts"

    def download_files(self):
        """Download city and hierarchy files"""
        super().download_files()  # Downloads city file
        self.downloader.download("hierarchy")  # Also need hierarchy file for index

    def build_indices(self):
        """Build required indices"""
        self.country_index = self.index_builder.build_country_index(self.options.get("quiet"))
        self.region_index = self.index_builder.build_region_index(self.options.get("quiet"))
        self.hierarchy_index = self.index_builder.build_hierarchy_index()
        self.city_index = self.index_builder.build_city_index(self.options.get("quiet"))

    def parse_item(self, item):
        """Parse district data"""
        # Filter by feature code - only import district types
        if item.get("featureCode") not in district_types:
            return None

        # Validate geonameid
        geonameid = self.validator.parse_int(item.get("geonameid"), "geonameid", entity_type="District")

        # Parse location
        location = self.validator.parse_location(item.get("latitude"), item.get("longitude"), entity_type="District")

        defaults = {
            "name": item["name"],
            "name_std": item.get("asciiName", ""),
            "location": location,
            "population": self.validator.parse_int(item.get("population"), "population", default=0),
        }

        # Add code if model supports it
        if hasattr(District, "code"):
            defaults["code"] = item.get("admin3Code", "")

        # Find city
        city = self._find_city(geonameid, defaults, item["name"])
        if not city:
            raise ValidationError(f"District: {defaults['name']}: Cannot find city -- skipping")

        defaults["city"] = city

        return {"id": geonameid, "defaults": defaults}

    def _find_city(self, geonameid, defaults, name):
        """
        Find city for district

        Args:
            geonameid: District geoname ID
            defaults: Dict with district data including location
            name: District name for logging

        Returns:
            City object or None
        """
        # Try hierarchy first
        try:
            city = self.city_index[self.hierarchy_index[geonameid]]
            self.logger.debug("Found city in hierarchy: %s [%d]", city.name, geonameid)
            return city
        except KeyError:
            self.logger.debug(
                "District: %d %s: Cannot find city in hierarchy, using nearest",
                geonameid,
                name,
            )

        # Fallback: Find nearest city using distance query
        city_pop_min = 100000

        # Try native distance query
        if Distance:
            try:
                city = (
                    City.objects.filter(
                        location__distance_lte=(
                            defaults["location"],
                            D(km=1000),
                        )
                    )
                    .annotate(distance=Distance("location", defaults["location"]))
                    .order_by("distance")
                    .first()
                )
                if city:
                    return city
            except Exception:
                pass

        # Fallback: Degree-based search for databases without distance support
        self.logger.warning(
            "District: %s: DB backend does not support native '.distance(...)' query "
            "falling back to two degree search",
            name,
        )
        search_deg = 2
        min_dist = float("inf")
        city = None

        bounds = Envelope(
            defaults["location"].x - search_deg,
            defaults["location"].y - search_deg,
            defaults["location"].x + search_deg,
            defaults["location"].y + search_deg,
        )

        for e in City.objects.filter(population__gt=city_pop_min).filter(location__intersects=bounds.wkt):
            dist = geo_distance(defaults["location"], e.location)
            if dist < min_dist:
                min_dist = dist
                city = e

        return city

    def create_or_update(self, parsed_data):
        """Create or update district record"""
        geonameid = parsed_data["id"]
        defaults = parsed_data["defaults"]

        # Check if district already exists (by city + name)
        try:
            with transaction.atomic():
                district = District.objects.get(city=defaults["city"], name=defaults["name"])

            # District exists but may not have correct geonameid as id
            # Update all attributes except id
            for key, value in defaults.items():
                setattr(district, key, value)
            district.save()
            created = False

        except District.DoesNotExist:
            # District doesn't exist, create it with geonameid as its id
            district, created = District.objects.update_or_create(id=geonameid, defaults=defaults)

        return district, created
