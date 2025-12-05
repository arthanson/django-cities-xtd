"""File download service for GeoNames data"""

import io
import logging
import os
from urllib.request import urlopen

from ..conf import settings
from ..exceptions import DownloadError

LOGGER_NAME = os.environ.get("TRAVIS_LOGGER_NAME", "cities")

# Download chunk size for streaming (8KB chunks)
DOWNLOAD_CHUNK_SIZE = 8192


class Downloader:
    """Handles downloading and caching of GeoNames data files"""

    def __init__(self, data_dir, force=False):
        """
        Initialize downloader

        Args:
            data_dir: Directory to store downloaded files
            force: If True, download even if file exists
        """
        self.data_dir = data_dir
        self.force = force
        self.logger = logging.getLogger(LOGGER_NAME)

    def download(self, filekey):
        """
        Download files for the given filekey

        Args:
            filekey: Key from settings.files dict (e.g., 'country', 'city')

        Raises:
            DownloadError: If download fails and file doesn't exist locally
        """
        if "filename" in settings.files[filekey]:
            filenames = [settings.files[filekey]["filename"]]
        else:
            filenames = settings.files[filekey]["filenames"]

        for filename in filenames:
            self._download_file(filekey, filename)

    def _download_file(self, filekey, filename):
        """Download a single file"""
        filepath = os.path.join(self.data_dir, filename)

        # Skip download if file exists and not forcing
        if not self.force and os.path.exists(filepath):
            self.logger.debug("File already exists: %s", filepath)
            return

        # Attempt download from URLs
        web_file = self._fetch_from_urls(filekey, filename)

        if web_file is not None:
            self._save_file(filename, web_file)
        elif not os.path.exists(filepath):
            urls = [e.format(filename=filename) for e in settings.files[filekey]["urls"]]
            raise DownloadError(f"File not found and download failed: {filename} {urls}")

    def _fetch_from_urls(self, filekey, filename):
        """Attempt to fetch file from list of URLs"""
        urls = [e.format(filename=filename) for e in settings.files[filekey]["urls"]]

        for url in urls:
            try:
                # Add timeout to prevent indefinite hangs
                web_file = urlopen(url, timeout=settings.file_download_timeout)

                # Check content type
                if "html" in web_file.headers.get("Content-Type", ""):
                    raise DownloadError(f"Content type of downloaded file was {web_file.headers['Content-Type']}")

                self.logger.debug("Downloaded: %s", url)
                return web_file

            except Exception as e:
                self.logger.debug("Failed to download from %s: %s", url, e)
                continue

        self.logger.error("Web file not found: %s. Tried URLs:\n%s", filename, "\n".join(urls))
        return None

    def _save_file(self, filename, web_file):
        """Save downloaded file to disk with streaming and size limits"""
        filepath = os.path.join(self.data_dir, filename)

        # Create directory if needed
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            self.logger.debug("Created directory: %s", self.data_dir)

        # Stream file to disk with size checking
        # This prevents memory exhaustion and DoS attacks
        self.logger.debug("Saving: %s", filepath)
        downloaded_size = 0
        max_size = settings.max_download_size

        with io.open(filepath, "wb") as f:
            while True:
                chunk = web_file.read(DOWNLOAD_CHUNK_SIZE)
                if not chunk:
                    break

                downloaded_size += len(chunk)
                if downloaded_size > max_size:
                    # Remove partial file
                    f.close()
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    raise DownloadError(
                        f"File {filename} exceeds maximum download size of {max_size} bytes "
                        f"({max_size / (1024**3):.1f}GB). Downloaded {downloaded_size} bytes before stopping."
                    )

                f.write(chunk)

        self.logger.debug("Saved %d bytes to %s", downloaded_size, filepath)
