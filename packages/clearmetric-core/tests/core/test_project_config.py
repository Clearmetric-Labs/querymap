from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from clearmetric.core.errors import ProjectConfigError
from clearmetric.core.project import load_project_config

from tests.wedge.helpers import write_policy

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "lineage"
    / "projects"
    / "jaffle_shop"
)


def _write_project(tmp_path: Path, payload: dict) -> Path:
    config_path = tmp_path / "clearmetric.yaml"
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    write_policy(tmp_path)
    return config_path


def test_missing_yaml_raises(tmp_path: Path):
    with pytest.raises(ProjectConfigError, match="Project config not found"):
        load_project_config(tmp_path)


def test_empty_sources_raises(tmp_path: Path):
    _write_project(
        tmp_path,
        {
            "version": 1,
            "dialect": "postgres",
            "sources": {},
            "posture": "strict",
            "policy": {"rules": "./policy/rules.yaml"},
        },
    )
    with pytest.raises(ProjectConfigError, match="at least one source"):
        load_project_config(tmp_path)


def test_bad_path_raises(tmp_path: Path):
    _write_project(
        tmp_path,
        {
            "version": 1,
            "dialect": "postgres",
            "sources": {"dbt": {"manifest": "./missing/manifest.json"}},
            "posture": "strict",
            "policy": {"rules": "./policy/rules.yaml"},
        },
    )
    with pytest.raises(ProjectConfigError, match="Configured path does not exist"):
        load_project_config(tmp_path)


def test_valid_load_resolves_manifest(tmp_path: Path):
    manifest = FIXTURE_ROOT / "manifest.json"
    target = tmp_path / "target"
    target.mkdir()
    (target / "manifest.json").write_text(
        manifest.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _write_project(
        tmp_path,
        {
            "version": 1,
            "dialect": "postgres",
            "sources": {"dbt": {"manifest": "./target/manifest.json"}},
            "posture": "strict",
            "policy": {"rules": "./policy/rules.yaml"},
        },
    )
    project = load_project_config(tmp_path)
    assert project.dialect == "postgres"
    assert project.sources.dbt is not None
    manifest_path = project.sources.dbt.manifest
    assert manifest_path is not None
    assert Path(manifest_path).is_file()


def test_snowflake_warehouse_kind_rejected(tmp_path: Path):
    manifest = FIXTURE_ROOT / "manifest.json"
    target = tmp_path / "target"
    target.mkdir()
    (target / "manifest.json").write_text(
        manifest.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _write_project(
        tmp_path,
        {
            "version": 1,
            "dialect": "postgres",
            "sources": {
                "warehouse": {"kind": "snowflake", "profile": "default"},
                "dbt": {"manifest": "./target/manifest.json"},
            },
            "posture": "strict",
            "policy": {"rules": "./policy/rules.yaml"},
        },
    )
    with pytest.raises(ProjectConfigError, match="failed validation"):
        load_project_config(tmp_path)


def test_missing_aliases_path_raises(tmp_path: Path):
    manifest = FIXTURE_ROOT / "manifest.json"
    target = tmp_path / "target"
    target.mkdir()
    (target / "manifest.json").write_text(
        manifest.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _write_project(
        tmp_path,
        {
            "version": 1,
            "dialect": "postgres",
            "sources": {"dbt": {"manifest": "./target/manifest.json"}},
            "posture": "strict",
            "policy": {"rules": "./policy/rules.yaml"},
            "aliases": "./missing_aliases.yaml",
        },
    )
    with pytest.raises(ProjectConfigError, match="does not exist"):
        load_project_config(tmp_path)


def test_invalid_policy_rules_raises(tmp_path: Path):
    manifest = FIXTURE_ROOT / "manifest.json"
    target = tmp_path / "target"
    target.mkdir()
    (target / "manifest.json").write_text(
        manifest.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _write_project(
        tmp_path,
        {
            "version": 1,
            "dialect": "postgres",
            "sources": {"dbt": {"manifest": "./target/manifest.json"}},
            "posture": "strict",
            "policy": {"rules": "./policy/rules.yaml"},
        },
    )
    (tmp_path / "policy" / "rules.yaml").write_text("not: [valid", encoding="utf-8")
    with pytest.raises(ProjectConfigError, match="Policy rules failed validation"):
        load_project_config(tmp_path)
