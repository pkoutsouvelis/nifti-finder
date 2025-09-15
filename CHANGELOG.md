# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog],
and this project adheres to [Semantic Versioning].

## [Unreleased]

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

[Unreleased]: https://github.com/<your-org>/<your-repo>/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/<your-org>/<your-repo>/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/<your-org>/<your-repo>/releases/tag/v1.0.0