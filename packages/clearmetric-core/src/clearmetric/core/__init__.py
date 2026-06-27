"""Public package surface for clearmetric-core."""

from __future__ import annotations

from ._version import __version__
from .aliases import load_table_alias_map
from .errors import (
    AliasMapError,
    CanonicalIdError,
    ClearMetricError,
    MergeConflictError,
)
from .ids import (
    asset_id,
    column_id,
    cte_id,
    leaf_name,
    measure_id,
    model_id,
    normalize_identifier,
    normalize_identifier_part,
    normalize_identifier_parts,
    page_id,
    report_id,
    schema_name,
    split_qualified_identifier,
    table_id,
    visual_id,
)
from .interop import (
    AliasMap,
    apply_alias_map,
    normalize_fqn_for_matching,
    resolve_table_match,
    warehouse_table_fqn_candidates,
    warehouse_table_fqn_candidates_from_name,
)
from .merge import merge
from .models import CatalogArtifact, Edge, Evidence, MatchStatus, Node, Warning
from .serialize import render_json

__all__ = [
    "__version__",
    "AliasMap",
    "AliasMapError",
    "MatchStatus",
    "apply_alias_map",
    "asset_id",
    "CatalogArtifact",
    "ClearMetricError",
    "CanonicalIdError",
    "column_id",
    "cte_id",
    "Edge",
    "Evidence",
    "leaf_name",
    "load_table_alias_map",
    "measure_id",
    "merge",
    "normalize_fqn_for_matching",
    "MergeConflictError",
    "model_id",
    "Node",
    "page_id",
    "normalize_identifier",
    "normalize_identifier_part",
    "normalize_identifier_parts",
    "render_json",
    "report_id",
    "resolve_table_match",
    "schema_name",
    "split_qualified_identifier",
    "table_id",
    "visual_id",
    "warehouse_table_fqn_candidates",
    "warehouse_table_fqn_candidates_from_name",
    "Warning",
]
