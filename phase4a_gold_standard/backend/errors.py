"""Domain errors with stable HTTP mappings."""

from __future__ import annotations

from typing import Any, Mapping


class BackendError(Exception):
    """Base class for errors safe to expose through the API."""

    status_code = 400
    code = "backend_error"

    def __init__(self, message: str, *, details: Mapping[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = dict(details or {})


class ValidationError(BackendError):
    code = "validation_error"
    status_code = 422


class NotFoundError(BackendError):
    code = "not_found"
    status_code = 404


class ConflictError(BackendError):
    code = "conflict"
    status_code = 409


class PermissionDeniedError(BackendError):
    code = "permission_denied"
    status_code = 403


class AuthenticationError(BackendError):
    code = "authentication_required"
    status_code = 401
