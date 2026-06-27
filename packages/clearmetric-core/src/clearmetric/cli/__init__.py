"""ClearMetric Core CLI — ``cm`` command router."""

from __future__ import annotations

import argparse
import json
import sys

from clearmetric.core import __version__, render_json
from clearmetric.lineage import (
    build_catalog_artifact,
    build_lineage_map,
    trace_downstream,
    trace_upstream,
)
from clearmetric.lineage.errors import LineageError
from clearmetric.lineage.render.mermaid import render_traversal_mermaid
from clearmetric.lineage.render.text import render_text, render_traversal_tree


def _build_root_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cm",
        description="ClearMetric Core — local compiler, graph engine, and CLI.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"cm {__version__} (ClearMetric Core)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser(
        "compile",
        help="Compile project input into a catalog graph artifact (JSON).",
    )
    compile_parser.add_argument(
        "project_input",
        help="Path to a dbt manifest.json file or a folder of UTF-8 .sql files.",
    )
    compile_parser.add_argument(
        "--dialect",
        required=True,
        help="sqlglot dialect name, for example postgres, snowflake, tsql, or bigquery.",
    )
    compile_parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format (default: json).",
    )

    impact_parser = subparsers.add_parser(
        "impact",
        help="Trace upstream or downstream column lineage for one selection.",
    )
    impact_parser.add_argument(
        "selection",
        help="Dataset column selection, for example orders.amount.",
    )
    impact_parser.add_argument(
        "project_input",
        help="Path to a dbt manifest.json file or a folder of UTF-8 .sql files.",
    )
    impact_parser.add_argument(
        "--dialect",
        required=True,
        help="sqlglot dialect name, for example postgres, snowflake, tsql, or bigquery.",
    )
    traversal = impact_parser.add_mutually_exclusive_group(required=True)
    traversal.add_argument(
        "--upstream",
        action="store_true",
        help="Trace upstream lineage for the selection.",
    )
    traversal.add_argument(
        "--downstream",
        action="store_true",
        help="Trace downstream impact for the selection.",
    )
    impact_parser.add_argument(
        "--format",
        choices=("text", "json", "mermaid"),
        default="text",
        help="Output format (default: text).",
    )
    return parser


def _run_compile(args: argparse.Namespace) -> int:
    if args.format == "json":
        artifact = build_catalog_artifact(args.project_input, dialect=args.dialect)
        print(json.dumps(render_json(artifact), indent=2, sort_keys=False))
    else:
        lineage_map = build_lineage_map(args.project_input, dialect=args.dialect)
        print(render_text(lineage_map))
    return 0


def _run_impact(args: argparse.Namespace) -> int:
    direction = "upstream" if args.upstream else "downstream"
    if direction == "upstream":
        result = trace_upstream(
            args.project_input,
            dialect=args.dialect,
            selection=args.selection,
        )
    else:
        result = trace_downstream(
            args.project_input,
            dialect=args.dialect,
            selection=args.selection,
        )

    if args.format == "json":
        print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=False))
        return 0

    artifact = build_catalog_artifact(args.project_input, dialect=args.dialect)
    if args.format == "mermaid":
        print(
            render_traversal_mermaid(
                result.selection_id,
                artifact,
                direction=direction,
            )
        )
        return 0

    print(
        render_traversal_tree(
            result,
            artifact,
            direction=direction,
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_root_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "compile":
            return _run_compile(args)
        if args.command == "impact":
            return _run_impact(args)
    except LineageError as exc:
        print(f"cm error: {exc}", file=sys.stderr)
        return 1

    print(f"cm: unknown command {args.command!r}", file=sys.stderr)
    return 1


__all__ = ["main"]
