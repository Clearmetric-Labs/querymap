"""Power BI module errors."""

from __future__ import annotations

from clearmetric.core.errors import ClearMetricError


class PowerBIError(ClearMetricError):
    """Base error for clearmetric-core."""


class PowerBIInputError(PowerBIError):
    """Invalid or missing user input."""


class PowerBIStructureError(PowerBIError):
    """PBIP/PBIR folder structure is corrupt or unsupported."""


__all__ = ["PowerBIError", "PowerBIInputError", "PowerBIStructureError"]
