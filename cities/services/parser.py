"""Data parsing service for GeoNames files"""

import io
import os
import zipfile

from ..conf import settings


class Parser:
    """Parses GeoNames data files into dictionaries"""

    def __init__(self, data_dir):
        """
        Initialize parser

        Args:
            data_dir: Directory containing downloaded files
        """
        self.data_dir = data_dir

    def get_data(self, filekey):
        """
        Parse files for the given filekey into dictionaries

        Args:
            filekey: Key from settings.files dict (e.g., 'country', 'city')

        Yields:
            dict: Parsed row with field names as keys
        """
        if "filename" in settings.files[filekey]:
            filenames = [settings.files[filekey]["filename"]]
        else:
            filenames = settings.files[filekey]["filenames"]

        for filename in filenames:
            yield from self._parse_file(filekey, filename)

    def _parse_file(self, filekey, filename):
        """Parse a single file"""
        name, ext = filename.rsplit(".", 1)

        # Handle zip files
        if ext == "zip":
            filepath = os.path.join(self.data_dir, filename)
            with zipfile.ZipFile(filepath) as zf:
                with zf.open(name + ".txt", "r") as zip_member:
                    file_obj = io.TextIOWrapper(zip_member, encoding="utf-8")
                    yield from self._parse_lines(filekey, file_obj)
        else:
            # Handle plain text files
            filepath = os.path.join(self.data_dir, filename)
            with io.open(filepath, "r", encoding="utf-8") as file_obj:
                yield from self._parse_lines(filekey, file_obj)

    def _parse_lines(self, filekey, file_obj):
        """Parse lines from file object"""
        fields = settings.files[filekey]["fields"]

        for row in file_obj:
            # Skip comment lines
            if row.startswith("#"):
                continue

            # Split on tabs and create dict
            values = row.rstrip("\n").split("\t")
            yield dict(zip(fields, values))
