class DomainError(Exception):
    """Base de errores de dominio."""


class NotFoundError(DomainError):
    """El recurso no existe."""


class PermissionDeniedError(DomainError):
    """El user no es dueno del recurso."""


class ValidationError(DomainError):
    """Datos invalidos."""


class ConflictError(DomainError):
    """Conflicto de estado (ej: sesion ya finalizada)."""
