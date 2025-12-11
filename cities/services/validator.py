"""Validation utilities for data import"""

import logging
import os

from django.contrib.gis.geos import Point

from ..exceptions import ValidationError

LOGGER_NAME = os.environ.get("TRAVIS_LOGGER_NAME", "cities")


class Validator:
    """Centralizes validation logic for import data"""

    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)

    def parse_int(self, value, field_name, default=None, entity_type=None):
        """
        Safely parse integer with error handling

        Args:
            value: Value to parse
            field_name: Name of field for error messages
            default: Default value if parsing fails (None = raise error)
            entity_type: Type of entity for error messages

        Returns:
            int: Parsed integer value

        Raises:
            ValidationError: If parsing fails and no default provided
        """
        try:
            return int(value)
        except (ValueError, TypeError):
            if default is not None:
                return default

            msg = f"Invalid {field_name}: {value}"
            if entity_type:
                msg = f"{entity_type}: {msg}"
            raise ValidationError(msg)

    def require_field(self, item, field_name, entity_type=None):
        """
        Require field to exist in item dict

        Args:
            item: Dictionary containing data
            field_name: Required field name
            entity_type: Type of entity for error messages

        Returns:
            Value from item dict

        Raises:
            ValidationError: If field is missing
        """
        try:
            return item[field_name]
        except KeyError:
            msg = f"Missing required field '{field_name}'"
            if entity_type:
                msg = f"{entity_type}: {msg}"
            raise ValidationError(msg)

    def parse_float(self, value, field_name, default=None, entity_type=None):
        """
        Safely parse float with error handling

        Args:
            value: Value to parse
            field_name: Name of field for error messages
            default: Default value if parsing fails (None = raise error)
            entity_type: Type of entity for error messages

        Returns:
            float: Parsed float value

        Raises:
            ValidationError: If parsing fails and no default provided
        """
        try:
            return float(value)
        except (ValueError, TypeError):
            if default is not None:
                return default

            msg = f"Invalid {field_name}: {value}"
            if entity_type:
                msg = f"{entity_type}: {msg}"
            raise ValidationError(msg)

    def parse_location(self, latitude, longitude, entity_type=None):
        """
        Parse and validate location coordinates

        Args:
            latitude: Latitude value (string or number)
            longitude: Longitude value (string or number)
            entity_type: Type of entity for error messages

        Returns:
            Point: Django Point object

        Raises:
            ValidationError: If coordinates are invalid
        """
        try:
            lat = float(latitude)
            lon = float(longitude)

            # Validate ranges
            if not (-90 <= lat <= 90):
                raise ValueError(f"Latitude {lat} out of range [-90, 90]")
            if not (-180 <= lon <= 180):
                raise ValueError(f"Longitude {lon} out of range [-180, 180]")

            return Point(lon, lat)

        except (ValueError, TypeError) as e:
            msg = f"Invalid coordinates ({latitude}, {longitude}): {e}"
            if entity_type:
                msg = f"{entity_type}: {msg}"
            raise ValidationError(msg)

    def lookup_foreign_key(self, index, key, relation_name, entity_type=None):
        """
        Look up foreign key in index with error handling

        Args:
            index: Dictionary index (e.g., country_index)
            key: Key to look up
            relation_name: Name of relation for error messages (e.g., "Country")
            entity_type: Type of entity for error messages

        Returns:
            Object from index

        Raises:
            ValidationError: If key not found in index
        """
        try:
            return index[key]
        except KeyError:
            msg = f"Cannot find {relation_name}: {key}"
            if entity_type:
                msg = f"{entity_type}: {msg}"
            raise ValidationError(msg)

    def parse_bool(self, value):
        """
        Parse boolean from string/int

        Args:
            value: Value to parse (1, "1", True, etc.)

        Returns:
            bool: Parsed boolean
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, str):
            return value.strip() in ("1", "true", "True", "TRUE", "yes", "Yes", "YES")
        return bool(value)
