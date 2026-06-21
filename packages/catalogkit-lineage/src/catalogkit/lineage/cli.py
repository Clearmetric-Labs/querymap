"""CLI entrypoint for catalogkit-lineage."""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .api import (
    build_catalog_artifact,
    build_lineage_map,
    build_openlineage_export,
    render_json,
    render_text,
    trace_downstream,
    trace_upstream,
)
from .errors import LineageError
from .render.mermaid import render_traversal_mermaid
from .render.text import render_traversal_tree


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="catalogkit-lineage",
        description="Build deterministic project-level lineage from a dbt manifest or SQL folder.",
    )
    parser.add_argument(
        "project_input",
        help="Path to a dbt manifest.json file or a folder of UTF-8 .sql files.",
    )
    parser.add_argument(
        "--dialect",
        required=True,
        help="sqlglot dialect name, for example postgres, snowflake, tsql, or bigquery.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "openlineage", "mermaid"),
        default="text",
        help="Renderer output format.",
    )
    traversal = parser.add_mutually_exclusive_group()
    traversal.add_argument(
        "--upstream",
        help="Dataset column selection to trace upstream, for example customers.customer_lifetime_value.",
    )
    traversal.add_argument(
        "--downstream",
        help="Dataset column selection to trace downstream, for example raw_payments.amount.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.format == "openlineage":
            if args.upstream or args.downstream:
                raise LineageError(
                    "Traversal flags cannot be combined with --format openlineage."
                )
            payload = build_openlineage_export(
                args.project_input,
                dialect=args.dialect,
            )
            print(json.dumps(payload, indent=2, sort_keys=False))
            return 0

        if args.upstream:
            result = trace_upstream(
                args.project_input,
                dialect=args.dialect,
                selection=args.upstream,
            )
            if args.format == "json":
                print(
                    json.dumps(
                        result.model_dump(mode="json"), indent=2, sort_keys=False
                    )
                )
            elif args.format == "mermaid":
                artifact = build_catalog_artifact(
                    args.project_input, dialect=args.dialect
                )
                print(
                    render_traversal_mermaid(
                        result.selection_id,
                        artifact,
                        direction="upstream",
                    )
                )
            else:
                artifact = build_catalog_artifact(
                    args.project_input, dialect=args.dialect
                )
                print(
                    render_traversal_tree(
                        result,
                        artifact,
                        direction="upstream",
                    )
                )
            return 0

        if args.downstream:
            result = trace_downstream(
                args.project_input,
                dialect=args.dialect,
                selection=args.downstream,
            )
            if args.format == "json":
                print(
                    json.dumps(
                        result.model_dump(mode="json"), indent=2, sort_keys=False
                    )
                )
            elif args.format == "mermaid":
                artifact = build_catalog_artifact(
                    args.project_input, dialect=args.dialect
                )
                print(
                    render_traversal_mermaid(
                        result.selection_id,
                        artifact,
                        direction="downstream",
                    )
                )
            else:
                artifact = build_catalog_artifact(
                    args.project_input, dialect=args.dialect
                )
                print(
                    render_traversal_tree(
                        result,
                        artifact,
                        direction="downstream",
                    )
                )
            return 0

        if args.format == "mermaid":
            raise LineageError(
                "Renderer format mermaid requires --upstream or --downstream."
            )

        artifact = build_lineage_map(args.project_input, dialect=args.dialect)
        if args.format == "json":
            print(json.dumps(render_json(artifact), indent=2, sort_keys=False))
        else:
            print(render_text(artifact))
        return 0
    except (LineageError, OSError) as exc:
        print(f"catalogkit-lineage error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
