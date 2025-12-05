"""Postal code importer"""

import re

from django.db import transaction
from django.db.models import Q

from ..conf import VALIDATE_POSTAL_CODES, settings
from ..exceptions import ValidationError
from ..models import District, PostalCode, Region, Subregion
from .base import BaseImporter


class PostalCodeImporter(BaseImporter):
    """Imports postal code data from GeoNames"""

    def __init__(self, command, options):
        super().__init__(command, options)
        self.num_existing_postal_codes = 0
        self.districts_to_delete = []

    def get_file_key(self):
        return "postal_code"

    def get_model_class(self):
        return PostalCode

    def get_description(self):
        return "Importing postal codes"

    def build_indices(self):
        """Build required indices"""
        self.country_index = self.index_builder.build_country_index(self.options.get("quiet"))
        self.region_index = self.index_builder.build_region_index(self.options.get("quiet"))

        if VALIDATE_POSTAL_CODES:
            self.postal_code_regex_index = self.index_builder.build_postal_code_regex_index(
                self.country_index, self.options.get("quiet")
            )

    def load_data(self):
        """Load data and check if optimization can be used"""
        self.num_existing_postal_codes = PostalCode.objects.count()
        if self.num_existing_postal_codes == 0:
            self.logger.debug("Zero postal codes found - using only-create postal code optimization")

        return super().load_data()

    def parse_item(self, item):
        """Parse postal code data"""
        country_code = item.get("countryCode")

        # Filter by configured countries
        if country_code not in settings.postal_codes and "ALL" not in settings.postal_codes:
            return None

        # Get postal code
        code = self.validator.require_field(item, "postalCode", "PostalCode")

        # Look up country
        country = self.validator.lookup_foreign_key(
            self.country_index, country_code, "Country", entity_type="PostalCode"
        )

        # Validate postal code against country regex
        if VALIDATE_POSTAL_CODES and self.postal_code_regex_index[country_code].match(code) is None:
            self.logger.warning("Postal code didn't validate: %s (%s)", code, country_code)
            return None

        # Parse location
        try:
            location = self.validator.parse_location(
                item.get("latitude"), item.get("longitude"), entity_type="PostalCode"
            )
        except ValidationError:
            location = None

        # Warn about long names
        place_name = item.get("placeName", "")
        if len(place_name) >= 200:
            self.logger.warning("Postal code name has more than 200 characters: %s", item)

        return {
            "country": country,
            "country_code": country_code,
            "code": code,
            "place_name": place_name,
            "region_name": item.get("admin1Name", ""),
            "region_code": item.get("admin1Code", ""),
            "subregion_name": item.get("admin2Name", ""),
            "subregion_code": item.get("admin2Code", ""),
            "district_name": item.get("admin3Name", ""),
            "district_code": item.get("admin3Code", ""),
            "location": location,
            "item": item,  # Keep original for hooks
        }

    def create_or_update(self, parsed_data):
        """Create or update postal code record"""
        country = parsed_data["country"]
        code = parsed_data["code"]
        place_name = parsed_data["place_name"]
        region_name = parsed_data["region_name"]
        region_code = parsed_data["region_code"]
        subregion_name = parsed_data["subregion_name"]
        subregion_code = parsed_data["subregion_code"]
        district_name = parsed_data["district_name"]
        district_code = parsed_data["district_code"]
        location = parsed_data["location"]

        # If postal codes exist, try to find existing one using query strategies
        if self.num_existing_postal_codes > 0:
            pc = self._find_existing_postal_code(
                country,
                code,
                place_name,
                region_name,
                region_code,
                subregion_name,
                subregion_code,
                district_name,
                district_code,
                location,
            )
        else:
            pc = None

        # Create new postal code if not found
        if pc is None:
            self.logger.debug("Creating postal code: %s", parsed_data["item"])
            pc = PostalCode(
                country=country,
                code=code,
                name=place_name,
                region_name=region_name,
                subregion_name=subregion_name,
                district_name=district_name,
            )
            created = True
        else:
            created = False

        # Lookup region, subregion, district relationships
        self._link_regions(pc)

        # Set location
        if location:
            pc.location = location

        pc.save()

        return pc, created

    def _find_existing_postal_code(
        self,
        country,
        code,
        place_name,
        region_name,
        region_code,
        subregion_name,
        subregion_code,
        district_name,
        district_code,
        location,
    ):
        """Try multiple query strategies to find existing postal code"""
        # Build Q objects for name-based queries
        reg_name_q = Q(region_name__iexact=region_name)
        subreg_name_q = Q(subregion_name__iexact=subregion_name)
        dst_name_q = Q(district_name__iexact=district_name)

        # Add code-based queries if relationships exist
        if hasattr(PostalCode, "region"):
            reg_name_q |= Q(region__code=region_code)
        if hasattr(PostalCode, "subregion"):
            subreg_name_q |= Q(subregion__code=subregion_code)
        if hasattr(PostalCode, "district") and hasattr(District, "code"):
            dst_name_q |= Q(district__code=district_code)

        # Define query strategies in order of specificity
        postal_code_args = (
            {"args": (reg_name_q, subreg_name_q, dst_name_q), "country": country, "code": code, "location": location},
            {"args": (reg_name_q, subreg_name_q, dst_name_q), "country": country, "code": code},
            {
                "args": (reg_name_q, subreg_name_q, dst_name_q),
                "country": country,
                "code": code,
                "name__iexact": re.sub("'", "", place_name),
            },
            {"args": tuple(), "country": country, "region__code": region_code},
            {
                "args": tuple(),
                "country": country,
                "code": code,
                "name": place_name,
                "region__code": region_code,
                "subregion__code": subregion_code,
            },
            {
                "args": tuple(),
                "country": country,
                "code": code,
                "name": place_name,
                "region__code": region_code,
                "subregion__code": subregion_code,
                "district__code": district_code,
            },
            {
                "args": tuple(),
                "country": country,
                "code": code,
                "name": place_name,
                "region_name": region_name,
                "subregion_name": subregion_name,
            },
            {
                "args": tuple(),
                "country": country,
                "code": code,
                "name": place_name,
                "region_name": region_name,
                "subregion_name": subregion_name,
                "district_name": district_name,
            },
        )

        # Try each query strategy until we find a match
        for args_dict in postal_code_args:
            try:
                return PostalCode.objects.get(
                    *args_dict["args"],
                    **{k: v for k, v in args_dict.items() if k != "args"},
                )
            except PostalCode.DoesNotExist:
                continue
            except PostalCode.MultipleObjectsReturned:
                pcs = PostalCode.objects.filter(
                    *args_dict["args"],
                    **{k: v for k, v in args_dict.items() if k != "args"},
                )
                self.logger.debug("Multiple postal codes found: %s", pcs)
                raise

        return None

    def _link_regions(self, pc):
        """Link postal code to region, subregion, district"""
        # Link region
        if pc.region_name != "":
            try:
                with transaction.atomic():
                    pc.region = Region.objects.get(
                        Q(name_std__iexact=pc.region_name) | Q(name__iexact=pc.region_name),
                        country=pc.country,
                    )
            except Region.DoesNotExist:
                pc.region = None
        else:
            pc.region = None

        # Link subregion
        if pc.subregion_name != "":
            try:
                with transaction.atomic():
                    pc.subregion = Subregion.objects.get(
                        Q(region__name_std__iexact=pc.region_name) | Q(region__name__iexact=pc.region_name),
                        Q(name_std__iexact=pc.subregion_name) | Q(name__iexact=pc.subregion_name),
                        region__country=pc.country,
                    )
            except Subregion.DoesNotExist:
                pc.subregion = None
        else:
            pc.subregion = None

        # Link district
        if pc.district_name != "":
            try:
                with transaction.atomic():
                    pc.district = District.objects.get(
                        Q(city__region__name_std__iexact=pc.region_name) | Q(city__region__name__iexact=pc.region_name),
                        Q(name_std__iexact=pc.district_name) | Q(name__iexact=pc.district_name),
                        city__country=pc.country,
                    )
            except District.MultipleObjectsReturned:
                # Handle duplicate districts - use one from same city
                pc.district = self._resolve_duplicate_districts(pc)
            except District.DoesNotExist:
                pc.district = None
        else:
            pc.district = None

        # Link city from district
        if pc.district is not None:
            pc.city = pc.district.city
        else:
            pc.city = None

    def _resolve_duplicate_districts(self, pc):
        """Handle multiple districts with same name"""
        districts = District.objects.filter(
            Q(city__region__name_std__iexact=pc.region_name) | Q(city__region__name__iexact=pc.region_name),
            Q(name_std__iexact=pc.district_name) | Q(name__iexact=pc.district_name),
            city__country=pc.country,
        )

        self.logger.debug("Multiple districts found: %s", districts.values_list("id", flat=True))

        # If they're all part of the same city, use the one with lower ID
        if districts.values_list("city").distinct().count() == 1:
            district_to_keep = districts.order_by("city__id").first()
            district_to_delete_id = districts.order_by("city__id").last().id
            self.districts_to_delete.append(district_to_delete_id)
            return district_to_keep
        else:
            raise District.MultipleObjectsReturned("Multiple districts in different cities")

    def cleanup(self):
        """Delete duplicate districts marked for deletion"""
        if self.districts_to_delete:
            District.objects.filter(id__in=self.districts_to_delete).delete()
            self.logger.info("Deleted %d duplicate districts", len(self.districts_to_delete))
