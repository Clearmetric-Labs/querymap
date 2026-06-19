# Release Checklist

Before publishing `querymap`, verify the public package surface end to end.

## Repository

- confirm git is initialized in the public package directory
- confirm the root `.gitignore` excludes local, generated, and build artifacts
- confirm no generated metadata directories are tracked as source-of-truth
- confirm governance files are present and production-ready

## Contract

- confirm the supported statement contract matches code, tests, and README
- confirm unsupported statement shapes fail loudly
- confirm deferred features are described as deferred, not implied
- confirm warnings remain part of the public contract

## Package Content

- confirm the package has no imports from enterprise code
- confirm docs and examples expose no proprietary logic
- confirm fixtures are generic and safe to publish
- confirm the public API surface is intentionally small

## Validation

- run package-local tests
- run the CLI against the bundled example fixture in text and JSON formats
- build sdist and wheel
- run `twine check dist/*`
- install from the built wheel in a fresh virtual environment
- run the README commands exactly as written

## Release Readiness

- confirm the README matches the shipped behavior exactly
- confirm package metadata is complete enough for PyPI consumers
- confirm PyPI Trusted Publishing is configured for `.github/workflows/publish.yml`
  with the `pypi` environment
- confirm the package description distinguishes `querymap` from the unrelated
  `sqlmap` security tool
