"""Package-specific errors for clearmetric-core."""

from __future__ import annotations


class LineageError(Exception):
    """Base class for clearmetric-core failures."""


class LineageInputError(LineageError):
    """Raised when the top-level project input is invalid or unsupported."""


class LineageContractError(LineageError):
    """Raised when supported input cannot satisfy the current public contract."""
