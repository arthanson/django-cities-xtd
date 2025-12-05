"""Base importer class providing template pattern for all importers"""

import logging
import os
from abc import ABC, abstractmethod

from tqdm import tqdm

from ..conf import HookException, settings
from ..exceptions import ValidationError
from ..services import Downloader, IndexBuilder, Parser, Validator

LOGGER_NAME = os.environ.get("TRAVIS_LOGGER_NAME", "cities")


class BaseImporter(ABC):
    """
    Base class for all entity importers

    Provides template method pattern for consistent import workflow:
    1. Download files
    2. Load and parse data
    3. Build indices
    4. Import records with hooks and error handling
    5. Cleanup
    """

    def __init__(self, command, options):
        """
        Initialize importer

        Args:
            command: Django management command instance
            options: Command line options dict
        """
        self.command = command
        self.options = options
        self.logger = logging.getLogger(LOGGER_NAME)

        # Initialize services
        self.downloader = Downloader(command.data_dir, force=options.get("force", False))
        self.parser = Parser(command.data_dir)
        self.validator = Validator()
        self.index_builder = IndexBuilder(command.data_dir, quiet=options.get("quiet", False))

        # Indices (populated by build_indices())
        self.country_index = None
        self.region_index = None
        self.city_index = None
        self.geo_index = None
        self.hierarchy_index = None
        self.postal_code_regex_index = None
        self.continent_index = None

    def run(self):
        """
        Main entry point - template method defining import workflow
        """
        # 1. Download files
        self.download_files()

        # 2. Load and parse data
        data = self.load_data()

        # 3. Build required indices
        self.build_indices()

        # 4. Import records
        self.import_records(data)

        # 5. Cleanup
        self.cleanup()

    @abstractmethod
    def get_file_key(self):
        """
        Return file key for download (e.g., 'country', 'city')

        Returns:
            str: Key from settings.files dict
        """
        pass

    @abstractmethod
    def get_model_class(self):
        """
        Return Django model class for this importer

        Returns:
            Model: Django model class
        """
        pass

    @abstractmethod
    def parse_item(self, item):
        """
        Parse raw item dict into model defaults dict

        Args:
            item: Raw data dict from parser

        Returns:
            dict: Parsed data ready for create/update, or None to skip

        Raises:
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    def create_or_update(self, parsed_data):
        """
        Create or update database record

        Args:
            parsed_data: Parsed data dict from parse_item()

        Returns:
            tuple: (object, created) where created is True if new
        """
        pass

    def get_description(self):
        """
        Get description for progress bar

        Returns:
            str: Description (e.g., "Importing countries")
        """
        return f"Importing {self.get_model_class()._meta.verbose_name_plural}"

    def get_hook_prefix(self):
        """
        Get prefix for hook names (e.g., "country" for "country_pre", "country_post")

        Returns:
            str: Hook prefix
        """
        return self.get_model_class()._meta.model_name

    def download_files(self):
        """Download required files"""
        self.downloader.download(self.get_file_key())

    def load_data(self):
        """
        Load and parse data file

        Returns:
            list: List of parsed data dicts
        """
        return list(self.parser.get_data(self.get_file_key()))

    def build_indices(self):
        """
        Build required indices

        Override in subclasses to build specific indices needed.
        Call parent implementation to get common indices like country_index.
        """
        pass

    def import_records(self, data):
        """
        Main import loop with hooks and error handling

        Args:
            data: List of parsed data dicts
        """
        total = len(data)

        for item in tqdm(
            data,
            disable=self.options.get("quiet"),
            total=total,
            desc=self.get_description(),
        ):
            try:
                # Pre-hook
                if not self.call_hook("pre", item):
                    continue

                # Parse and validate
                parsed = self.parse_item(item)
                if parsed is None:
                    continue

                # Create/update
                obj, created = self.create_or_update(parsed)

                # Post-hook
                if not self.call_hook("post", obj, item):
                    continue

                # Log
                self.log_result(obj, created)

            except ValidationError as e:
                self.logger.warning("%s", e)
                continue

            except Exception as e:
                self.logger.error("Error processing item: %s", e, exc_info=True)
                continue

    def call_hook(self, hook_type, *args, **kwargs):
        """
        Call plugin hooks

        Args:
            hook_type: Hook type ('pre' or 'post')
            *args: Arguments to pass to hook
            **kwargs: Keyword arguments to pass to hook

        Returns:
            bool: True if should continue, False if should skip
        """
        hook_name = f"{self.get_hook_prefix()}_{hook_type}"

        if hasattr(settings, "plugins"):
            for plugin in settings.plugins.get(hook_name, []):
                try:
                    func = getattr(plugin, hook_name)
                    func(self.command, *args, **kwargs)
                except HookException as e:
                    error = str(e)
                    if error:
                        self.logger.error(error)
                    return False

        return True

    def log_result(self, obj, created):
        """
        Log import result

        Args:
            obj: Created/updated object
            created: True if object was created, False if updated
        """
        action = "Added" if created else "Updated"
        self.logger.debug("%s %s: %s", action, self.get_model_class()._meta.verbose_name, obj)

    def cleanup(self):
        """
        Cleanup after import (e.g., delete indices)

        Override in subclasses if cleanup is needed.
        """
        pass
