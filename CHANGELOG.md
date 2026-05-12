# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog],
and this project adheres to [Semantic Versioning].

## [Unreleased]

## [1.2.0] - 2026-05-12
### Added
- New table-based filters in `nifti_finder.filters.extra_filters`:
  - `IncludeFromTable` / `ExcludeFromTable`: include/exclude files based on an
    `id` column (and optional criteria column) of a CSV/TSV table (e.g.
    BIDS `participants.tsv`).
  - `IncludeFromLogs` / `ExcludeFromLogs`: include/exclude files based on
    log-style records.
- `nifti_finder.filters.utils` helpers (e.g. `parse_scalar`) shared across
  table/log filters.

### Changed
- Reorganized the `filters` package:
  - Filters previously in `filters/unit.py` are now split into
    `filters/basic_filters.py` (suffix/prefix/regex/extension/exists) and
    `filters/extra_filters.py` (table/log-based).
- Test layout updated to match the new module split:
  - `tests/filters/test_basic_filters.py`
  - `tests/filters/test_extra_filters.py`

### Removed
- Deprecated `NiftiExplorer` shim class. Use `NeuroExplorer` instead.
- Deprecated `stage_1_pattern` / `stage_2_pattern` keyword arguments on
  `NeuroExplorer`. Use `outer` / `inner` instead.
- Old `filters/unit.py` module and `tests/filters/test_filters.py`
  (replaced by the basic/extra split above).

## [1.1.0] - 2025-09-15
### Added
- New arguments `outer` and `inner` for `NeuroExplorer`, replacing `stage_1_pattern` and `stage_2_pattern`.
- Deprecation utilities:
  - `@deprecated_class` decorator to mark classes as deprecated and emit warnings on instantiation.
  - `@deprecated_alias` decorator to shim old keyword arguments to new ones with warnings.

### Changed
- `NeuroExplorer` now uses clearer terminology:
  - `outer`: Glob pattern for first-level search scope (datasets/subjects/sessions).
  - `inner`: Glob pattern for files/directories within each `outer` scope.

### Deprecated
- `NiftiExplorer` is deprecated; use `NeuroExplorer` instead. Functionality remains the same.
  - A shim class remains available until **v1.2.0**.
- Arguments `stage_1_pattern` and `stage_2_pattern` are deprecated.
  - Use `outer` and `inner` instead.
  - Support will be removed in **v1.2.0**.

## [1.0.0] - 2025-09-14
### Added
- Initial stable release with:
  - `BasicFileExplorer`, `TwoStageFileExplorer` file explorers with globbing support for any dataset structure.
  - Filter system (`FilterableMixin`) with logical composition (`ComposeFeature`) and multiple include/exclude filters.
  - Support for materializing file exploration results (`MaterializeMixin`) 
  - `NiftiExplorer` and `AllPurposeFileExplorer` core API for file exploration including two-stage, filtering and materialization support. 

---

[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/
[Semantic Versioning]: https://semver.org/spec/v2.0.0.html

[Unreleased]: https://github.com/pkoutsouvelis/nifti-finder/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/pkoutsouvelis/nifti-finder/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/pkoutsouvelis/nifti-finder/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/pkoutsouvelis/nifti-finder/releases/tag/v1.0.0
