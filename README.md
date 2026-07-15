[![PyPI version](https://img.shields.io/pypi/v/nifti-finder.svg)](https://pypi.org/project/nifti-finder/)
[![Python versions](https://img.shields.io/pypi/pyversions/nifti-finder.svg)](https://pypi.org/project/nifti-finder/)
![License](https://img.shields.io/badge/license-Apache%202.0-blue)
[![CI](https://github.com/pkoutsouvelis/nifti-finder/actions/workflows/ci.yml/badge.svg)](https://github.com/pkoutsouvelis/nifti-finder/actions/workflows/ci.yml)


## nifti-finder

Navigate neuroimaging datasets (and more) using flexible file explorers and filters. 
Optimized for typical neuroimaging research workflows, including BIDS-structured datasets.


## Key features

- **Flexible file discovery** with glob-based pattern matching for any dataset structure. 
- Rich set of **composable filters** for precise dataset querying (by file extension, prefix/suffix, regex, existence of related files, etc.).
- **Extensible design** with modular, reusable interfaces for creating custom explorers and filters


## Installation

```bash
pip install nifti-finder
# or from source
pip install -e .
```


## Quickstart

#### Get all NIfTI files from any nested dataset

```python
from nifti_finder import FileFinder

from your_package import preprocess

# Default: finds all .nii and .nii.gz files (flat recursive scan)
finder = FileFinder()

for path in finder.scan("/path/to/dataset"):
    preprocess(path)
```

#### Track subject-level progress in BIDS-style datasets

```python
finder = FileFinder(
    levels={"subjects": "sub-*"},       # directory levels (progress tracks the first)
    patterns="**/anat/*T1w.nii*",        # file patterns at the final stage
)

for path in finder.scan("/path/to/dataset", progress=True, desc="Subjects"):
    preprocess(path)
```

Output:

```txt
Subjects:  50%|███████████████████▌               | 30/60 [00:15<00:15,  2.00 it/s]
```

#### Exclude subjects with missing data; e.g., a segmentation mask

```python
from nifti_finder.filters import IncludeIfFileExists

finder = FileFinder(
    levels={"subjects": "sub-*"},
    patterns="**/anat/*T1w.nii*",
    filters=[
        IncludeIfFileExists(
            filename_pattern="*seg*", # require a segmentation mask
            search_in="/labels",      # in a parallel labels/ tree
            mirror_relative_to="/path/to/dataset",
        )
    ],
)

for path in finder.scan("/path/to/dataset"):
    preprocess(path)
```


## API Overview

- **Recommended**
  - `FileFinder` — nested or flat file discovery with `levels`, `patterns`, filters, and materialization helpers.
- **Primitives**
  - `RecursiveFileExplorer` — flat recursive glob.
  - `NestedFileExplorer` — multi-level directory traversal with optional progress; uses `patterns` at the final stage.
- **Deprecated (removed in v2.2.0)**
  - `NeuroExplorer` — legacy `outer` / `inner` two-stage API.
  - `AllPurposeFileExplorer`, `BasicFileExplorer`, `TwoStageFileExplorer`.
- **Filters**
  - Include/Exclude: `Extension`, `FilePrefix`, `FileSuffix`, `FileRegex`, `DirectoryPrefix/Suffix/Regex`, `IfFileExists`
  - Filters can be combined with logical operators (`AND`/`OR`).
- **Mixins & Interfaces**
  - `MaterializeMixin` — utilities to list, deduplicate, sort, batch, or count matches.
  - `FilterableMixin` — add, remove, and compose filters dynamically.


## Extended Examples

### Multi-level directory traversal

```python
finder = FileFinder(
    levels={
        "datasets": "OpenNeuro-ds*",
        "subjects": "sub-*",
        "sessions": "ses-*",
        "anat": "anat",
    },
    patterns=["*_T1w.nii*", "*_FLAIR.nii*"],
)

for path in finder.scan("/path/to/datasets", progress=True, desc="Datasets"):
    preprocess(path)
```

### Use with non-NIfTI files (e.g., JSON)

```python
finder = FileFinder(
    levels={"subjects": "sub-*"},
    patterns="**/*.json",
)
for p in finder.scan("/path/to/bids", progress=True, desc="Subjects"):
    print(p)
```

Explorers support multiple patterns and filters, but will traverse once per pattern.

### Materialize results

`FileFinder` provides convenience methods to turn the streaming output of `scan()` into concrete Python data structures.

This is useful when you want:
- A list of paths (with optional sorting, deduplication, or limiting)
- A single path (first match)
- A quick boolean check
- A count
- Iteration in batches

```python
finder = FileFinder(
    levels={"subjects": "sub-*"},
    patterns="**/anat/*T1w.nii*",
)
paths = finder.list("/path/to/dataset", sort=True, unique=True)
```

### Chainable filtering

`FileFinder` allows include/exclude filters to refine results.

```python
from nifti_finder.filters import IncludeExtension, ExcludeDirPrefix

finder = FileFinder(
    patterns="**/*.nii*",
    filters=[
        ExcludeFileSuffix("preprocessed"),              # drop already preprocessed files
        ExcludeDirPrefix("bad"),                        # drop 'bad' files
        IncludeIfFileExists(filename_pattern="*mask*"), # keep if a brain mask exists in same directory
    ],
    logic="AND",                                        # combination logic
)

for path in finder.scan("/path/to/dataset"):
    preprocess(path)
```

Filters can be dynamically adjusted.

```python
finder.add_filters(ExcludeFileSuffix("mask"))
finder.remove_filters(ExcludeFileSuffix("mask"))
finder.clear_filters()
```

Filters can be composed together to get their own combination logic.

```python
from nifti_finder.filters import ComposeFilter, ExcludeFilePrefix

suffix_filter = ComposeFilter(
    filters=[ExcludeFileSuffix("bet"), ExcludeFileSuffix("mask")],
    logic="OR"
)
prefix_filter = ComposeFilter(
    filters=[ExcludeFileSuffix("pet"), ExcludeFileSuffix("dwi")],
    logic="OR"
)
filename_filter = ComposeFilter(
    filters=[suffix_filter, prefix_filter],
    logic="AND"
)
finder.add_filters(filename_filter)
```

### Migrating from v1.x

| v1.x | v2.0 |
|------|------|
| `NeuroExplorer()` | `FileFinder()` (flat scan; no progress bar) |
| `NeuroExplorer(outer="sub-*", inner="**/*.nii*")` | `FileFinder(levels={"subjects": "sub-*"}, patterns="**/*.nii*")` |
| `AllPurposeFileExplorer(pattern="*.json")` | `FileFinder(patterns="*.json")` |
| `pattern=` | `patterns=` |

Legacy shims (`NeuroExplorer`, `AllPurposeFileExplorer`, etc.) remain available until **v2.2.0**.


## Development

```bash
# Setup
pip install -e .[test]

# Run tests
pytest -q
```
