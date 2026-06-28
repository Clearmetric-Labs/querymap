"""Catalog projection emitter."""

from __future__ import annotations

import json

from clearmetric.compiler.models import CompiledGraph
from clearmetric.core import render_json
from clearmetric.projection import project_catalog_assets


def emit_catalog(compiled: CompiledGraph) -> str:
    catalog = project_catalog_assets(compiled.artifact)
    return json.dumps(render_json(catalog), indent=2, sort_keys=False)
