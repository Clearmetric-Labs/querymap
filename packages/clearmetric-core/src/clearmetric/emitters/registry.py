"""Emitter registry."""

from __future__ import annotations

from clearmetric.compiler.models import CompiledGraph
from clearmetric.core.errors import EmitterError

from .catalog import emit_catalog
from .json import emit_json
from .openlineage import emit_openlineage
from .text import emit_text

_COMPILE_FORMATS = {
    "json": emit_json,
    "text": emit_text,
    "openlineage": emit_openlineage,
    "catalog": emit_catalog,
}


def emit_compile(format: str, compiled: CompiledGraph) -> str:
    handler = _COMPILE_FORMATS.get(format)
    if handler is None:
        raise EmitterError(f"unsupported compile format: {format}")
    return handler(compiled)
