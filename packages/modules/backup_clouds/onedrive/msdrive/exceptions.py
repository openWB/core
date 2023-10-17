class DriveException(Exception):
    """There was an ambiguous exception that occurred"""


class InvalidAccessToken(DriveException):
    """Invalid access token"""


class ItemNotFound(DriveException):
    """Item not found"""


class RateLimited(DriveException):
    """Rate limit exceeded"""
