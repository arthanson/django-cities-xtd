"""Index building service for fast lookups during import"""

import logging
import os
import re
from itertools import chain

from swapper import load_model
from tqdm import tqdm

from ..models import District, Region, Subregion
from .parser import Parser

# Load swappable models
Continent = load_model("cities", "Continent")
Country = load_model("cities", "Country")
City = load_model("cities", "City")

LOGGER_NAME = os.environ.get("TRAVIS_LOGGER_NAME", "cities")


class IndexBuilder:
    """Builds in-memory indices for fast lookups during import"""

    def __init__(self, data_dir=None, quiet=False):
        """
        Initialize index builder

        Args:
            data_dir: Directory containing data files (for hierarchy)
            quiet: If True, disable progress bars
        """
        self.data_dir = data_dir
        self.quiet = quiet
        self.logger = logging.getLogger(LOGGER_NAME)

    @staticmethod
    def build_continent_index(quiet=False):
        """
        Build continent code -> Continent object index

        Returns:
            dict: {code: Continent object}
        """
        return {c.code: c for c in Continent.objects.all()}

    @staticmethod
    def build_country_index(quiet=False):
        """
        Build country code -> Country object index

        Returns:
            dict: {code: Country object}
        """
        country_index = {}
        countries_qs = Country.objects.all()
        total = countries_qs.count()

        for obj in tqdm(
            countries_qs.iterator(),
            disable=quiet,
            total=total,
            desc="Building country index",
        ):
            country_index[obj.code] = obj

        return country_index

    @staticmethod
    def build_region_index(quiet=False):
        """
        Build region full_code -> Region/Subregion object index

        Returns:
            dict: {full_code: Region/Subregion object}
        """
        region_index = {}

        # Fetch querysets once and calculate total count efficiently
        regions_qs = Region.objects.all().select_related("country")
        subregions_qs = Subregion.objects.all().select_related("region__country")
        total = regions_qs.count() + subregions_qs.count()

        for obj in tqdm(
            chain(
                regions_qs.iterator(),
                subregions_qs.iterator(),
            ),
            disable=quiet,
            total=total,
            desc="Building region index",
        ):
            region_index[obj.full_code()] = obj

        return region_index

    @staticmethod
    def build_city_index(quiet=False):
        """
        Build city id -> City object index

        Returns:
            dict: {id: City object}
        """
        city_index = {}
        cities_qs = City.objects.all()
        cities_count = cities_qs.count()

        for obj in tqdm(
            cities_qs.iterator(chunk_size=1000),
            disable=quiet,
            total=cities_count,
            desc="Building city index",
        ):
            city_index[obj.id] = obj

        return city_index

    def build_hierarchy_index(self):
        """
        Build hierarchy parent-child index from hierarchy file

        Returns:
            dict: {child_id: parent_id}
        """
        if not self.data_dir:
            raise ValueError("data_dir required for building hierarchy index")

        parser = Parser(self.data_dir)
        # Load data once into memory to avoid double file parsing
        data = list(parser.get_data("hierarchy"))
        total = len(data)

        hierarchy = {}
        for item in tqdm(
            data,
            disable=self.quiet,
            total=total,
            desc="Building hierarchy index",
        ):
            parent_id = int(item["parent"])
            child_id = int(item["child"])
            hierarchy[child_id] = parent_id

        return hierarchy

    @staticmethod
    def build_geo_index(quiet=False):
        """
        Build comprehensive geoname_id -> object index for all geographic types

        Returns:
            dict: {geoname_id: {"type": Model, "object": instance}}
        """
        geo_index = {}

        for type_ in (Country, Region, Subregion, City, District):
            plural_type_name = (
                "{}s".format(type_.__name__) if type_.__name__[-1] != "y" else "{}ies".format(type_.__name__[:-1])
            )

            # Fetch queryset once and calculate count efficiently
            # Use select_related to prefetch foreign keys that will be accessed
            qs = type_.objects.all()
            if type_ == Region:
                qs = qs.select_related("country")
            elif type_ == Subregion:
                qs = qs.select_related("region__country")
            elif type_ == City:
                qs = qs.select_related("country", "region", "subregion")
            elif type_ == District:
                qs = qs.select_related("city__country", "city__region", "city__subregion")

            total_count = qs.count()
            for obj in tqdm(
                qs.iterator(chunk_size=1000),
                disable=quiet,
                total=total_count,
                desc="Building geo index for {}".format(plural_type_name.lower()),
            ):
                geo_index[obj.id] = {
                    "type": type_,
                    "object": obj,
                }

        return geo_index

    def build_postal_code_regex_index(self, country_index, quiet=False):
        """
        Build postal code regex index from country data

        Args:
            country_index: Country index from build_country_index()
            quiet: If True, disable progress bars

        Returns:
            dict: {country_code: compiled_regex}
        """
        postal_code_regex_index = {}

        for code, country in tqdm(
            country_index.items(),
            disable=quiet,
            total=len(country_index),
            desc="Building postal code regex index",
        ):
            try:
                postal_code_regex_index[code] = re.compile(country.postal_code_regex)
            except Exception as e:
                self.logger.error("Couldn't compile postal code regex for %s: %s", country.code, e.args)
                postal_code_regex_index[code] = ""

        return postal_code_regex_index
