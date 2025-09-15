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
from nifti_finder.explorers import NeuroExplorer

from your_package import preprocess

# Default: finds all .nii and .nii.gz files
explorer = NeuroExplorer()

for path in explorer.scan("/path/to/dataset"):
    preprocess(path)
```

#### Track subject-level progress in BIDS-style datasets

```python
explorer = NeuroExplorer(
    outer="sub-*",              # level to compute progress (e.g., root/sub-*/...)
    inner="**/anat/*T1w.nii*",  # rest (e.g., ses-*/anat/T1w.nii.gz)
)

for path in explorer.scan("/path/to/dataset", progress=True, desc="Subjects"):
    preprocess(path)
```

Output:

```txt
Subjects:  50%|███████████████████▌               | 30/60 [00:15<00:15,  2.00 it/s]
```

#### Exclude subjects with missing data; e.g., a segmentation mask

```python
from nifti_finder.filters import IncludeIfFileExists

explorer = NeuroExplorer(
    outer="sub-*",
    inner="**/anat/*T1w.nii*",
    filters=[
        IncludeIfFileExists(
            filename_pattern="*seg*", # require a segmentation mask
            search_in="/labels",      # in a parallel labels/ tree
            mirror_relative_to="/path/to/dataset",
        )
    ],
)

for path in explorer.scan("/path/to/dataset"):
    preprocess(path)
```


## API Overview

- **Explorers**
  - `AllPurposeFileExplorer` - general-purpose scanning with patterns + filters.
  - `NeuroExplorer` - two-stage scanning (outer/inner) with patterns + filters + progress tracking, optimized for neuroimaging workflows.
- **Filters**
  - Include/Exclude: `Extension`, `FilePrefix`, `FileSuffix`, `FileRegex`, `DirectoryPrefix/Suffix/Regex`, `IfFileExists`
  - Filters can be combined with logical operators (`AND`/`OR`).
- **Mixins & Interfaces**
  - `BasicFileExplorer` & `TwoStageFileExplorer` for file traversal
  - `MaterializeMixin` — utilities to list, deduplicate, sort, batch, or count matches.
  - `FilterableMixin` — add, remove, and compose filters dynamically.


## Extended Examples

### Use with non-NIfTI files (e.g., JSON)

```python
explorer = NeuroExplorer(outer="sub-*", inner="**/*.json")
for p in explorer.scan("/path/to/bids", progress=True, desc="Subjects"):
    print(p)
```

Explorers support multiple patterns and filters, but will traverse once per pattern.

### General-purpose exploration

If you don’t want to assume any nested (subject/... or dataset/subject/...) hierarchy, use `AllPurposeFileExplorer` for flexible scanning.

```python
from nifti_finder.explorers import AllPurposeFileExplorer

explorer = AllPurposeFileExplorer(pattern="*.json")

for path in explorer.scan("/path/to/dataset"):
    print(path)
```

### Materialize results
Both `NeuroExplorer` and `AllPurposeExplorer` provide convenience methods to turn the streaming output of scan() into concrete Python data structures.

This is useful when you want:
- A list of paths (with optional sorting, deduplication, or limiting)
- A single path (first match)
- A quick boolean check
- A count
- Iteration in batches

```python
explorer = NeuroExplorer(outer="sub-*", inner="**/anat/*T1w.nii*")
paths = explorer.list("/path/to/dataset", sort=True, unique=True)
```

### Chainable filtering

Both `NeuroExplorer` and `AllPurposeExplorer` allow include/exclude filters to refine results.

```python
from nifti_finder.filters import IncludeExtension, ExcludeDirPrefix

explorer = AllPurposeFileExplorer(
    pattern="**/*.nii*",
    filters=[
        ExcludeFileSuffix("preprocessed"),              # drop already preprocessed files
        ExcludeDirPrefix("bad"),                        # drop 'bad' files
        IncludeIfFileExists(filename_pattern="*mask*"), # keep if a brain mask exists in same directory
    ],
    logic="AND",                                        # combination logic
)

for path in explorer.scan("/path/to/dataset"):
    preprocess(path)
```

Filters can be dynamically adjusted.

```python
explorer.add_filters(ExcludeFileSuffix("mask"))
explorer.remove_filters(ExcludeFileSuffix("mask"))
explorer.clear_filters()
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
explorer.add_filters(filename_filter)
```


## Development

```bash
# Setup
pip install -e .[test]

# Run tests
pytest -q
```