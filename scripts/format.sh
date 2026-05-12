#!/usr/bin/env bash
# Format and lint Python sources from the repository root.
# Install dev tools first, e.g. `pip install -e ".[dev]"` in your venv.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Prefer project venv so `ruff`, `black`, etc. resolve without activating manually.
if [[ -d "$ROOT/.venv/bin" ]]; then
  PATH="$ROOT/.venv/bin:$PATH"
fi

echo "Running Ruff..."
ruff check --fix .

echo "Running Docformatter..."
# Scope to `src/` only: docformatter only handles Python and can error on odd files at repo root.
# `--black` matches Black's wrapping; place paths before `-e` so argparse does not treat `.` as an exclude.
docformatter -r --in-place --black src

echo "Running Black..."
black .

echo "Checking doc coverage..."
# Source tree only (skip tests); config in root `pyproject.toml` under `[tool.interrogate]`.
interrogate src/nifti_finder

echo "Done."