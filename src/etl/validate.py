"""Validation module: check data quality and enforce business rules."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .settings import VALID_ENUMS, VALID_RANGES, ETLMode, LibraryLayout, Platform

logger = logging.getLogger(__name__)


class ValidationError:
    """Represents a single validation error."""

    def __init__(self, row_idx: int, column: str, value, rule: str, message: str):
        self.row_idx = row_idx
        self.column = column
        self.value = value
        self.rule = rule
        self.message = message

    def __repr__(self):
        return f"Row {self.row_idx}: {self.message}"


class ValidationResult:
    """Result of validation check."""

    def __init__(self, is_valid: bool, errors: List[ValidationError] = None):
        self.is_valid = is_valid
        self.errors = errors or []

    def __bool__(self):
        return self.is_valid


def validate_samples(samples_df: pd.DataFrame) -> ValidationResult:
    """Validate samples table."""
    errors = []

    # sample_id must be non-empty and unique
    nulls = samples_df[samples_df["sample_id"].isna()].index.tolist()
    if nulls:
        for idx in nulls:
            errors.append(
                ValidationError(
                    idx, "sample_id", None, "NOT_NULL",
                    f"sample_id is null at row {idx}"
                )
            )

    duplicates = samples_df[samples_df["sample_id"].duplicated()].index.tolist()
    if duplicates:
        for idx in duplicates:
            errors.append(
                ValidationError(
                    idx, "sample_id", samples_df.loc[idx, "sample_id"], "UNIQUE",
                    f"Duplicate sample_id '{samples_df.loc[idx, 'sample_id']}' at row {idx}"
                )
            )

    # platform must be valid
    valid_platforms = {e.value for e in Platform}
    invalid_platforms = samples_df[~samples_df["platform"].isin(valid_platforms)].index.tolist()
    if invalid_platforms:
        for idx in invalid_platforms:
            errors.append(
                ValidationError(
                    idx, "platform", samples_df.loc[idx, "platform"], "ENUM",
                    f"Invalid platform '{samples_df.loc[idx, 'platform']}' at row {idx}"
                )
            )

    # collection_date should not be in future
    today = datetime.utcnow().date()
    try:
        samples_df["collection_date_parsed"] = pd.to_datetime(samples_df["collection_date"], errors="coerce").dt.date
        future_dates = samples_df[samples_df["collection_date_parsed"] > today].index.tolist()
        if future_dates:
            for idx in future_dates:
                errors.append(
                    ValidationError(
                        idx, "collection_date", samples_df.loc[idx, "collection_date"], "FUTURE_DATE",
                        f"Collection date in future at row {idx}"
                    )
                )
    except Exception as e:
        logger.warning(f"Could not parse collection_date: {e}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def validate_runs(runs_df: pd.DataFrame) -> ValidationResult:
    """Validate runs table."""
    errors = []

    # run_id must be non-empty and unique
    nulls = runs_df[runs_df["run_id"].isna()].index.tolist()
    if nulls:
        for idx in nulls:
            errors.append(
                ValidationError(
                    idx, "run_id", None, "NOT_NULL",
                    f"run_id is null at row {idx}"
                )
            )

    duplicates = runs_df[runs_df["run_id"].duplicated()].index.tolist()
    if duplicates:
        for idx in duplicates:
            errors.append(
                ValidationError(
                    idx, "run_id", runs_df.loc[idx, "run_id"], "UNIQUE",
                    f"Duplicate run_id '{runs_df.loc[idx, 'run_id']}' at row {idx}"
                )
            )

    # sample_id must be non-null
    nulls = runs_df[runs_df["sample_id"].isna()].index.tolist()
    if nulls:
        for idx in nulls:
            errors.append(
                ValidationError(
                    idx, "sample_id", None, "NOT_NULL",
                    f"sample_id is null at row {idx}"
                )
            )

    # library_layout must be valid
    valid_layouts = {e.value for e in LibraryLayout}
    invalid_layouts = runs_df[~runs_df["library_layout"].isin(valid_layouts)].index.tolist()
    if invalid_layouts:
        for idx in invalid_layouts:
            errors.append(
                ValidationError(
                    idx, "library_layout", runs_df.loc[idx, "library_layout"], "ENUM",
                    f"Invalid library_layout '{runs_df.loc[idx, 'library_layout']}' at row {idx}"
                )
            )

    # read_length > 0
    try:
        read_lengths = pd.to_numeric(runs_df["read_length"], errors="coerce")
        invalid_read_length = runs_df[(read_lengths <= 0) | read_lengths.isna()].index.tolist()
        if invalid_read_length:
            for idx in invalid_read_length:
                errors.append(
                    ValidationError(
                        idx, "read_length", runs_df.loc[idx, "read_length"], "RANGE",
                        f"read_length must be > 0 at row {idx}"
                    )
                )
    except Exception as e:
        logger.warning(f"Could not validate read_length: {e}")

    # fastq_gb >= 0
    try:
        fastq_gb = pd.to_numeric(runs_df["fastq_gb"], errors="coerce")
        invalid_fastq_gb = runs_df[(fastq_gb < 0) | fastq_gb.isna()].index.tolist()
        if invalid_fastq_gb:
            for idx in invalid_fastq_gb:
                errors.append(
                    ValidationError(
                        idx, "fastq_gb", runs_df.loc[idx, "fastq_gb"], "RANGE",
                        f"fastq_gb must be >= 0 at row {idx}"
                    )
                )
    except Exception as e:
        logger.warning(f"Could not validate fastq_gb: {e}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def validate_qc_metrics(qc_df: pd.DataFrame) -> ValidationResult:
    """Validate QC metrics table."""
    errors = []

    # run_id must be non-empty
    nulls = qc_df[qc_df["run_id"].isna()].index.tolist()
    if nulls:
        for idx in nulls:
            errors.append(
                ValidationError(
                    idx, "run_id", None, "NOT_NULL",
                    f"run_id is null at row {idx}"
                )
            )

    # q30_rate in [0, 1]
    try:
        q30_rate = pd.to_numeric(qc_df["q30_rate"], errors="coerce")
        invalid_q30 = qc_df[(q30_rate < 0) | (q30_rate > 1) | q30_rate.isna()].index.tolist()
        if invalid_q30:
            for idx in invalid_q30:
                errors.append(
                    ValidationError(
                        idx, "q30_rate", qc_df.loc[idx, "q30_rate"], "RANGE",
                        f"q30_rate must be in [0, 1] at row {idx}"
                    )
                )
    except Exception as e:
        logger.warning(f"Could not validate q30_rate: {e}")

    # gc_percent in [0, 100]
    try:
        gc_percent = pd.to_numeric(qc_df["gc_percent"], errors="coerce")
        invalid_gc = qc_df[(gc_percent < 0) | (gc_percent > 100) | gc_percent.isna()].index.tolist()
        if invalid_gc:
            for idx in invalid_gc:
                errors.append(
                    ValidationError(
                        idx, "gc_percent", qc_df.loc[idx, "gc_percent"], "RANGE",
                        f"gc_percent must be in [0, 100] at row {idx}"
                    )
                )
    except Exception as e:
        logger.warning(f"Could not validate gc_percent: {e}")

    # duplication_rate in [0, 1]
    try:
        dup_rate = pd.to_numeric(qc_df["duplication_rate"], errors="coerce")
        invalid_dup = qc_df[(dup_rate < 0) | (dup_rate > 1) | dup_rate.isna()].index.tolist()
        if invalid_dup:
            for idx in invalid_dup:
                errors.append(
                    ValidationError(
                        idx, "duplication_rate", qc_df.loc[idx, "duplication_rate"], "RANGE",
                        f"duplication_rate must be in [0, 1] at row {idx}"
                    )
                )
    except Exception as e:
        logger.warning(f"Could not validate duplication_rate: {e}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def validate_foreign_keys(samples_df: pd.DataFrame, runs_df: pd.DataFrame) -> ValidationResult:
    """Validate FK constraint: runs.sample_id must exist in samples.sample_id."""
    errors = []

    valid_sample_ids = set(samples_df["sample_id"].dropna())
    invalid_fks = runs_df[~runs_df["sample_id"].isin(valid_sample_ids)].index.tolist()

    if invalid_fks:
        for idx in invalid_fks:
            errors.append(
                ValidationError(
                    idx, "sample_id", runs_df.loc[idx, "sample_id"], "FK_CHECK",
                    f"sample_id '{runs_df.loc[idx, 'sample_id']}' not found in samples at row {idx}"
                )
            )

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def validate_all(
    samples_df: pd.DataFrame,
    runs_df: pd.DataFrame,
    qc_df: pd.DataFrame,
    mode: ETLMode = ETLMode.STRICT,
) -> Tuple[bool, List[ValidationError]]:
    """
    Run all validations.
    
    Args:
        samples_df: Samples table
        runs_df: Runs table
        qc_df: QC metrics table
        mode: strict or quarantine
    
    Returns:
        (is_valid, list of errors)
    """
    all_errors = []

    # Validate each table
    for name, df, validator in [
        ("samples", samples_df, validate_samples),
        ("runs", runs_df, validate_runs),
        ("qc_metrics", qc_df, validate_qc_metrics),
    ]:
        result = validator(df)
        if not result.is_valid:
            logger.warning(f"{name} validation found {len(result.errors)} errors")
            all_errors.extend(result.errors)

    # Validate FK constraints
    fk_result = validate_foreign_keys(samples_df, runs_df)
    if not fk_result.is_valid:
        logger.warning(f"FK validation found {len(fk_result.errors)} errors")
        all_errors.extend(fk_result.errors)

    is_valid = len(all_errors) == 0

    if not is_valid:
        logger.error(f"Validation failed with {len(all_errors)} total errors")
        if mode == ETLMode.STRICT:
            logger.error("STRICT mode: stopping pipeline")
        else:
            logger.warning("QUARANTINE mode: will separate bad records")

    return is_valid, all_errors
