from __future__ import annotations

from pathlib import Path

from catalogkit.lineage import build_catalog_artifact
from catalogkit.lineage.coverage import coverage_summary
from catalogkit.lineage.loaders import load_project

FIXTURES_ROOT = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def main() -> int:
    dialects = _project_dialects()
    exit_code = 0
    for project_dir in sorted((FIXTURES_ROOT / "projects").iterdir()):
        if not project_dir.is_dir():
            continue
        project_input = (
            project_dir / "manifest.json"
            if (project_dir / "manifest.json").exists()
            else project_dir
        )
        dialect = dialects.get(project_input.resolve())
        if dialect is None:
            raise SystemExit(f"Missing dialect mapping for fixture: {project_input}")
        project = load_project(project_input, dialect=dialect)
        artifact = build_catalog_artifact(project_input, dialect=dialect)
        summary = coverage_summary(artifact, project)
        print(
            f"{project_dir.name}: total={summary['total']} "
            f"resolved={summary['resolved']} flagged={summary['flagged']} "
            f"source_leaf={summary['source_leaf']} silent={summary['silent']} "
            f"bogus_source_leaves={summary['bogus_source_leaves']}"
        )
        print(f"  warning_counts={summary['warning_counts']}")
        if summary["silent"] or summary["bogus_source_leaves"]:
            exit_code = 1
    return exit_code


def _project_dialects() -> dict[Path, str]:
    import sys

    package_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(package_root))
    from tests.ground_truth import project_dialects

    return project_dialects()


if __name__ == "__main__":
    raise SystemExit(main())
