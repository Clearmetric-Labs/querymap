"""CLI entrypoint for querymap."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .api import build_query_map, render_json, render_text
from .errors import QueryMapError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="querymap",
        description="Map one supported SQL statement into deterministic relation dependencies.",
    )
    parser.add_argument(
        "sql_file",
        help="Path to a UTF-8 SQL file containing exactly one supported statement.",
    )
    parser.add_argument(
        "--dialect",
        required=True,
        help="sqlglot dialect name, for example postgres, snowflake, tsql, or bigquery.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Renderer output format.",
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
        sql = Path(args.sql_file).read_text(encoding="utf-8")
        query_map = build_query_map(sql, dialect=args.dialect)
        if args.format == "json":
            print(json.dumps(render_json(query_map), indent=2, sort_keys=False))
        else:
            print(render_text(query_map))
        return 0
    except (OSError, QueryMapError) as exc:
        print(f"querymap error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
