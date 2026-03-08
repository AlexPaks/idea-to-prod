class ServiceError(Exception):
    """Base service error."""


class EntityNotFoundError(ServiceError):
    """Raised when a required entity does not exist."""


class InvalidRequestError(ServiceError):
    """Raised when request input is invalid for service-level constraints."""
