"""Extra filters extending the basic functionality."""

from __future__ import annotations

__all__ = [
    "IncludeFromTable",
    "IncludeFromLogs",
    "ExcludeFromTable",
    "ExcludeFromLogs",
]

from typing import Any, Sequence, Pattern, TypeAlias, cast
from pathlib import Path
from dataclasses import dataclass, field
import re
import csv
import warnings

from nifti_finder.filters.base import Filter
from nifti_finder.utils import resolve_path, get_ext
from nifti_finder.filters.utils import parse_scalar

CriteriaValue: TypeAlias = str | int | float | bool


@dataclass(frozen=True, slots=True)
class IncludeFromTable(Filter):
    """Include a file if it is included in an `id` column and optionally meets specific
    criteria, defined by another column.

    Useful for filtering BIDS-style datasets directly from the
    'participants.tsv' file.

    Behavior:
        - If `id_pattern` is provided, it defines how to search for IDs inside filepaths.
            Example: "sub-{id}_" -> matches 'sub-01_' safely, not 'sub-011_'.
        - If `id_pattern` is None, the whole filepath (fallback: stem, then name.ext)
            is used directly as the lookup key.
        - If no ID is found in the path, then return False, except if `skip_if_missing`
            is set to `False`.
        - If the ID is found in the path and its criteria column value matches `criteria_value`,
            then the file is included.

    Args:
        id_column:        The column to use as the id.
        criteria_column:  The column to use as the criteria. Optional, defaults to None.
        criteria_value:   The criteria to use to filter the file. Optional, required
                            if `criteria_column` is provided. Defaults to None.
        skip_if_missing:  If True, excludes files whose id is not present.
        id_pattern:       Optional path subset pattern with a {id} placeholder;
                            e.g., "sub-{id}_", or "/sub-{id}/", or "{id}_T1w".
                            Defaults to None: the filepath should exactly match the row id.
    """

    table_path: Path | str
    id_column: str
    criteria_column: str | None = None
    criteria_value: CriteriaValue | Sequence[CriteriaValue] | None = None
    skip_if_missing: bool = True
    id_pattern: str | None = None

    # Cached data for quick lookup
    _id_accept_map: dict[str, bool] = field(init=False, repr=False)
    _compiled_patterns: dict[str, Pattern[str]] | None = field(init=False, repr=False)

    def __post_init__(self):
        table_path = resolve_path(self.table_path)

        if self.id_pattern and "{id}" not in self.id_pattern:
            raise ValueError("id_pattern must contain a {id} placeholder")

        if self.criteria_column is not None and self.criteria_value is None:
            raise ValueError("criteria_column requires criteria_value")

        if self.criteria_column is None and self.criteria_value is not None:
            raise ValueError("criteria_value requires criteria_column")

        if not table_path.exists():
            raise FileNotFoundError(f"Table file {table_path} does not exist")

        delim = "\t" if table_path.suffix.lower() == ".tsv" else ","

        with table_path.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=delim)
            self._validate_columns(reader.fieldnames)

            # Cache which IDs match the criteria
            id_to_accept: dict[str, bool] = {}

            values_to_match = (
                self._normalize_criteria_values(self.criteria_value)
                if self.criteria_value is not None
                else None
            )

            for row in reader:
                row_id = str(row.get(self.id_column, "")).strip()
                if not row_id:
                    continue

                if self.criteria_column is None:
                    is_match = True
                else:
                    is_match = self._is_match(
                        row.get(self.criteria_column, None),
                        cast(list[Any], values_to_match),
                    )

                id_to_accept[row_id] = id_to_accept.get(row_id, False) or is_match

        object.__setattr__(self, "_id_accept_map", id_to_accept)

        # Compile patterns if id_pattern is provided
        if self.id_pattern:
            compiled: dict[str, Pattern[str]] = {}
            for row_id in id_to_accept.keys():
                compiled[row_id] = self._compile_id_pattern(row_id, self.id_pattern)
            object.__setattr__(self, "_compiled_patterns", compiled)
        else:
            object.__setattr__(self, "_compiled_patterns", None)

    def __call__(self, filepath: Path | str, /) -> bool:
        fp_path = Path(filepath)
        fp_str = str(fp_path)

        # Use pattern-based matching if available
        if self._compiled_patterns is not None:
            matched_ids = [
                _id for _id, p in self._compiled_patterns.items() if p.search(fp_str)
            ]
            # No match found.
            if not matched_ids:
                return not self.skip_if_missing

            if len(matched_ids) > 1:
                warnings.warn(
                    f"Multiple matches found for {fp_str}; "
                    f"checking for first one ({matched_ids[0]})",
                    UserWarning,
                )
            return self._id_accept_map[matched_ids[0]]

        # Whole path matching; try basename, stem, and full path in order
        for possible_id in (
            fp_str,
            fp_path.name,
            fp_path.name.replace(get_ext(fp_path), ""),  # stem
        ):
            if possible_id in self._id_accept_map:
                return self._id_accept_map[possible_id]

        # No match found
        return not self.skip_if_missing

    @staticmethod
    def _normalize_criteria_values(
        val: CriteriaValue | Sequence[CriteriaValue],
    ) -> list[Any]:
        """Normalize the provided criteria value(s) into a list of parsed scalars."""
        # Treat strings as scalars, not sequences
        if isinstance(val, str):
            vals = [val]
        elif isinstance(val, Sequence):
            vals = list(val)
        else:
            vals = [val]

        return [parse_scalar(v) for v in vals]

    def _validate_columns(self, fieldnames: Sequence[str] | None) -> None:
        """Validate required table columns."""
        if not fieldnames:
            raise ValueError(f"No header row found in table: {self.table_path}")

        required_columns = [self.id_column]

        if self.criteria_column is not None:
            required_columns.append(self.criteria_column)

        missing = [c for c in required_columns if c not in fieldnames]

        if missing:
            raise ValueError(
                f"Missing required column(s) {missing} in table: {self.table_path}. "
                f"Found columns: {fieldnames}"
            )

    def _is_match(self, raw_value: Any, values_to_match: list[Any]) -> bool:
        """Check if the raw value matches the provided criteria values."""
        val = parse_scalar(raw_value)

        for v in values_to_match:
            if isinstance(val, (int, float)) and isinstance(v, (int, float)):
                if float(val) == float(v):
                    return True
            else:
                if val == v:
                    return True

        return False

    def _compile_id_pattern(self, row_id: str, id_pattern: str) -> re.Pattern[str]:
        """Build a regex based on the specific row ID and provided `id_pattern`."""
        before, after = id_pattern.split("{id}")
        expr = re.escape(before) + re.escape(row_id) + re.escape(after)
        return re.compile(expr)


@dataclass(frozen=True, slots=True)
class IncludeFromLogs(Filter):
    """Include a file if it is present in a logs file.

    Optionally, a specific message can be required for inclusion.

    Expected log format:
        filepath[: message]

    Examples:
        /data/sub-01_T1w.nii.gz
        /data/sub-02_T1w.nii.gz: FAILED
        sub-03: SUCCESS

    Behavior:
        - If `message` is None, any occurrence of the file in the log
          is considered a match.
        - If `message` is provided, only entries with the matching
          message are considered valid.
        - Matching is attempted using:
            1. Full filepath string
            2. Basename
            3. Stem
        - If no match is found:
            - return False if `skip_if_missing=True`
            - return True otherwise

    Args:
        logs_path:       Path to the logs file.
        message:         Optional message filter (e.g., "FAILED").
        skip_if_missing: If True, exclude files not present in the logs.
    """

    logs_path: Path | str
    message: str | None = None
    skip_if_missing: bool = True

    # Cached lookup table
    _accept_map: dict[str, bool] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        logs_path = resolve_path(self.logs_path)

        if not logs_path.exists():
            raise FileNotFoundError(f"Logs file {logs_path} does not exist")

        accept_map: dict[str, bool] = {}

        with logs_path.open("r", encoding="utf-8") as f:
            for line_number, raw_line in enumerate(f, start=1):
                line = raw_line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Split into filepath and optional message
                if ":" in line:
                    file_entry, log_message = line.split(":", maxsplit=1)
                    file_entry = file_entry.strip()
                    log_message = log_message.strip()
                else:
                    file_entry = line
                    log_message = None

                if not file_entry:
                    warnings.warn(
                        f"Empty filepath entry in logs file {logs_path} at line {line_number}",
                        UserWarning,
                    )
                    continue

                # Match logic
                is_match = True if self.message is None else log_message == self.message

                accept_map[file_entry] = accept_map.get(file_entry, False) or is_match

        object.__setattr__(self, "_accept_map", accept_map)

    def __call__(self, filepath: Path | str, /) -> bool:
        fp_path = Path(filepath)
        fp_str = str(fp_path)

        # Try multiple lookup forms
        for possible_id in (
            fp_str,
            fp_path.name,
            fp_path.name.replace(get_ext(fp_path), ""),  # stem
        ):
            if possible_id in self._accept_map:
                return self._accept_map[possible_id]

        # No match found
        return not self.skip_if_missing


class ExcludeFromTable(IncludeFromTable):
    """Exclude a file if it is included in an `id` column and meets specific criteria,
    defined by another column.

    Opposite of `IncludeFromTable`. See `IncludeFromTable` for examples.

    Args:
        id_column:        The column to use as the id.
        criteria_column:  The column to use as the criteria.
        criteria_value:   The criteria to use to filter the file.
        skip_if_missing:  If True, includes files whose id is not present.
        id_pattern:       Optional path subset pattern with a {id} placeholder;
                            e.g., "sub-{id}_", or "/sub-{id}/", or "{id}_T1w"
    """

    def __call__(self, filepath: Path | str, /) -> bool:
        return not super().__call__(filepath)


class ExcludeFromLogs(IncludeFromLogs):
    """Exclude a file if it is present in a logs file.

    Optionally, a specific message can be required for exclusion.

    Opposite of `IncludeFromLogs`. See `IncludeFromLogs` for examples.

    Args:
        logs_path:        Path to the logs file.
        message:          Optional message filter (e.g., "FAILED").
        skip_if_missing:  If True, includes files not present in the logs.
    """

    def __call__(self, filepath: Path | str, /) -> bool:
        return not super().__call__(filepath)
