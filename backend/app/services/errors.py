class ServiceError(Exception):
    """Base service error."""


class EntityNotFoundError(ServiceError):
    """Raised when a required entity does not exist."""
