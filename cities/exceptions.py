"""Custom exceptions for django-cities importer"""


class ValidationError(Exception):
    """Raised when data validation fails during import"""

    pass


class DownloadError(Exception):
    """Raised when file download fails"""

    pass


class ParseError(Exception):
    """Raised when data parsing fails"""

    pass
