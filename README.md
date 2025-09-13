## nifti-finder

Navigate neuroimaging datasets (and more) with simple file explorers and filters. Optimized for NIfTI workflows but flexible enough for any file type by adjusting filename patterns.

- **Python**: >= 3.10
- **License**: Apache 2.0

### Installation

```bash
pip install nifti-finder
# or from source
pip install -e .
```

### Example usage

#### Explore NIfTI files with nested structure

```python
from nifti_finder.explorers import NiftiExplorer

# Default: finds all .nii and .nii.gz files
explorer = NiftiExplorer()

for path in explorer.scan("/path/to/dataset"):
    print(path)
```

#### Track subject-level progress in BIDS-style datasets

```python
from nifti_finder.explorers import NiftiExplorer
from nifti_finder.filters import ExcludeFileSuffix

from your_package import preprocess

explorer = NiftiExplorer(
    stage_1_pattern="sub-*",
    stage_2_pattern="**/anat/*T1w.nii*",
)

for path in explorer.scan("/path/to/dataset", progress=True, desc="Subjects"):
    preprocess(path)

```

Output:

```txt
Subjects:  50%|███████████████████▌               | 30/60 [00:15<00:15,  2.00 it/s]
```

#### Require a segmentation mask in a parallel labels/ tree

```python
from nifti_finder.explorers import NiftiExplorer
from nifti_finder.filters import IncludeIfFileExists

from your_package import preprocess

explorer = NiftiExplorer(
    stage_1_pattern="sub-*",
    stage_2_pattern="**/anat/*T1w.nii*",
    filters=[
        IncludeIfFileExists(
            filename_pattern="*seg*",
            search_in="/labels",
            mirror_relative_to="/path/to/dataset",
        )
    ],
)

for path in explorer.scan("/path/to/dataset"):
    preprocess(path)
```

### Extra functionality

#### Use with non-NIfTI files (e.g., JSON)

```python
from nifti_finder import NiftiExplorer, AllPurposeFileExplorer

explorer = NiftiExplorer(stage_1_pattern="sub-*", stage_2_pattern="**/*.json")
for p in explorer.scan("/path/to/bids", progress=True, desc="Subjects"):
    print(p)
```

Explorers support multiple patterns and filters, but will traverse once per pattern.

#### General-purpose exploration

If you don’t want to assume any nested (subject/... or dataset/subject/...) hierarchy, use `AllPurposeFileExplorer` for flexible scanning.

```python
from nifti_finder.explorers import AllPurposeFileExplorer

explorer = AllPurposeFileExplorer(pattern="*.json")

for path in explorer.scan("/path/to/dataset"):
    print(path)
```

#### Materializing Results
Both `NiftiExplorer` and `AllPurposeExplorer` provide convenience methods to turn the streaming output of scan() into concrete Python data structures.

This is useful when you want:
- A list of paths (with optional sorting, deduplication, or limiting)
- A single path (first match)
- A quick boolean check
- A count
- Iteration in batches

```python
from nifti_finder.explorers import NiftiExplorer

explorer = NiftiExplorer(stage_1_pattern="sub-*", stage_2_pattern="**/anat/*T1w.nii*")
paths = explorer.list("/path/to/dataset", sort=True, unique=True)
```

#### Filtering

Both `NiftiExplorer` and `AllPurposeExplorer` allow include/exclude filters to refine results.

```python
from nifti_finder.explorers import AllPurposeFileExplorer
from nifti_finder.filters import (
    IncludeExtension, ExcludeDirPrefix, IncludeIfFileExists
)

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
    print(path)
```

Filters can by dynamically adjusted.

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

### API Overview

- Explorers
  - `BasicFileExplorer` - pattern-only scanning (any structure).
  - `TwoStageFileExplorer` - pattern-only scanning with progress tracking (nested structure).
  - `AllPurposeFileExplorer` - pattern scanning + filters (any dataset structure)
  - `NiftiExplorer` - pattern scanning (preconfigured for NIfTI) + filters + progress tracking (nested structure)
- Filters (selected)
  - Include/Exclude: `Extension`, `FilePrefix`, `FileSuffix`, `FileRegex`, `DirectoryPrefix/Suffix/Regex`, `IfFileExists`


### Development

```bash
# Setup
pip install -e .[test]

# Run tests
pytest -q
```

### Why nifti-finder?

- Simple patterns for fast discovery
- Composable filters for precise control
- Flexible traversal with progress tracking for common neuroimaging layouts
- Works for any file types (not just NIfTI) by changing patterns