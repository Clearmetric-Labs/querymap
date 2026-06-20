# Development

## Editable Installs

Install the shared core first, then any tool package that depends on it:

```bash
python -m pip install -e packages/catalog-core
python -m pip install -e "packages/query-map[dev,release]"
```

## Tests

Run the full suite from the repository root:

```bash
pytest -v
```

Run package-focused tests:

```bash
pytest -v packages/catalog-core/tests
pytest -v packages/query-map/tests
```

## Builds

Build packages independently:

```bash
python -m build packages/catalog-core
python -m build packages/query-map
```
