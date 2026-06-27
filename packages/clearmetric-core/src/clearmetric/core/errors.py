"""Shared errors for clearmetric-core."""

from __future__ import annotations


class ClearMetricError(Exception):
    """Base class for clearmetric-core failures."""


class CanonicalIdError(ClearMetricError):
    """Raised when an identifier cannot be normalized into a canonical ID."""


class MergeConflictError(ClearMetricError):
    """Raised when artifacts cannot be merged without losing information."""


class AliasMapError(ClearMetricError):
    """Raised when a table alias file is invalid or unsupported."""
