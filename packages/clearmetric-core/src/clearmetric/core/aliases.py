"""Load versioned table alias files for cross-graph matching."""

from __future__ import annotations

from pathlib import Path

from .errors import AliasMapError
from .interop import AliasMap, normalize_fqn_for_matching

_SUPPORTED_VERSION = "1"


def load_table_alias_map(path: str | Path) -> AliasMap:
    """
    Load a version-1 alias file into an ``AliasMap``.

    Expected format::

        version: 1
        table_aliases:
          salesmart.dbo.orders: orders
    """
    file_path = Path(path).expanduser().resolve()
    if not file_path.is_file():
        raise AliasMapError(f"Alias file does not exist: {file_path}")

    version: str | None = None
    aliases: AliasMap = {}
    in_table_aliases = False

    for line_number, raw_line in enumerate(
        file_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("version:"):
            version = line.split(":", 1)[1].strip()
            if version != _SUPPORTED_VERSION:
                raise AliasMapError(
                    f"Unsupported alias file version {version!r} at {file_path}:{line_number}; "
                    f"expected {_SUPPORTED_VERSION!r}."
                )
            continue

        if line == "table_aliases:":
            in_table_aliases = True
            continue

        if not in_table_aliases:
            raise AliasMapError(
                f"Unexpected content at {file_path}:{line_number}; "
                "expected 'version:' and 'table_aliases:' sections."
            )

        if ":" not in line:
            raise AliasMapError(
                f"Invalid alias entry at {file_path}:{line_number}; "
                "expected 'source: target' form."
            )

        source, target = line.split(":", 1)
        source = source.strip()
        target = target.strip()
        if not source or not target:
            raise AliasMapError(
                f"Invalid alias entry at {file_path}:{line_number}; "
                "source and target must be non-empty."
            )

        normalized_source = normalize_fqn_for_matching(source)
        normalized_target = normalize_fqn_for_matching(target)
        if (
            normalized_source in aliases
            and aliases[normalized_source] != normalized_target
        ):
            raise AliasMapError(
                f"Duplicate alias key {normalized_source!r} with conflicting targets "
                f"at {file_path}:{line_number}."
            )
        aliases[normalized_source] = normalized_target

    if version is None:
        raise AliasMapError(f"Missing 'version:' in alias file: {file_path}")
    if not in_table_aliases:
        raise AliasMapError(
            f"Missing 'table_aliases:' section in alias file: {file_path}"
        )

    return aliases
