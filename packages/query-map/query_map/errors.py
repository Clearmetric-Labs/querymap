"""Package-specific errors for query-map."""

from __future__ import annotations


class QueryMapError(Exception):
    """Base class for query-map failures."""


class QueryMapParseError(QueryMapError):
    """Raised when SQL cannot be parsed into a supported AST."""


class QueryMapContractError(QueryMapError):
    """Raised when parsed SQL cannot be represented by the current contract."""
