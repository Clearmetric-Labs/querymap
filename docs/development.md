# Development

## Editable Install

```bash
python -m pip install -e "packages/clearmetric-core[dev,release]"
```

## Tests

Run the full suite from the repository root:

```bash
python -m pytest -v packages/clearmetric-core/tests tests/
```

Run repository boundary checks:

```bash
python -m pytest -v tests/test_repository_boundaries.py
python -m pytest -v tests/test_cross_package_artifacts.py
python -m pytest -v tests/test_module_independence.py
```

Lineage trust gate:

```bash
python -m pytest -v \
  packages/clearmetric-core/tests/lineage/test_corpus_invariants.py \
  packages/clearmetric-core/tests/lineage/test_ground_truth.py
PYTHONPATH=packages/clearmetric-core \
  python packages/clearmetric-core/scripts/sweep_lineage_coverage.py
```

## Builds

```bash
python -m build packages/clearmetric-core
python -m twine check packages/clearmetric-core/dist/*
```

Smoke test the installed wheel:

```bash
python -m venv .pkgsmoke
source .pkgsmoke/bin/activate
python -m pip install packages/clearmetric-core/dist/*.whl
cm --version
python -c "import clearmetric.core; import clearmetric.lineage; import clearmetric.query; import clearmetric.powerbi"
```
