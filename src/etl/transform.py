"""Transform module: normalize types, deduplicate, clean data."""

import logging
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def normalize_string_column(series: pd.Series, uppercase: bool = False) -> pd.Series:
    """Normalize string column: trim, replace nulls."""
    s = series.astype(str).str.strip()
    s = s.replace({"NA": None, "null": None, "NULL": None, "": None})
    if uppercase:
        s = s.str.upper()
    return s


def cast_numeric(series: pd.Series, dtype: str = "float64") -> pd.Series:
    """Safely cast to numeric, replacing invalid with NaN."""
    return pd.to_numeric(series, errors="coerce").astype(dtype)


def cast_date(series: pd.Series) -> pd.Series:
    """Safely cast to date."""
    return pd.to_datetime(series, errors="coerce").dt.date


def transform_samples(samples_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform samples table:
    - Normalize strings
    - Type casting
    - Deduplication (keep last)
    """
    logger.info("Transforming samples table")
    
    df = samples_df.copy()
    
    # Normalize string columns
    df["sample_id"] = normalize_string_column(df["sample_id"])
    df["project_id"] = normalize_string_column(df["project_id"])
    df["organism"] = normalize_string_column(df["organism"])
    df["tissue"] = normalize_string_column(df["tissue"])
    df["platform"] = normalize_string_column(df["platform"], uppercase=True)
    
    # Cast date
    df["collection_date"] = cast_date(df["collection_date"])
    
    # Deduplication (keep last occurrence)
    initial_rows = len(df)
    df = df.drop_duplicates(subset=["sample_id"], keep="last")
    dedup_count = initial_rows - len(df)
    if dedup_count > 0:
        logger.info(f"Removed {dedup_count} duplicate sample_id records")
    
    return df


def transform_runs(runs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform runs table:
    - Normalize strings
    - Type casting
    - Deduplication
    """
    logger.info("Transforming runs table")
    
    df = runs_df.copy()
    
    # Normalize string columns
    df["run_id"] = normalize_string_column(df["run_id"])
    df["sample_id"] = normalize_string_column(df["sample_id"])
    df["library_layout"] = normalize_string_column(df["library_layout"], uppercase=True)
    
    # Optional checksums
    if "md5_1" in df.columns:
        df["md5_1"] = normalize_string_column(df["md5_1"])
    if "md5_2" in df.columns:
        df["md5_2"] = normalize_string_column(df["md5_2"])
    
    # Numeric casting
    df["read_length"] = cast_numeric(df["read_length"], dtype="int64")
    df["fastq_gb"] = cast_numeric(df["fastq_gb"], dtype="float64")
    
    # Deduplication
    initial_rows = len(df)
    df = df.drop_duplicates(subset=["run_id"], keep="last")
    dedup_count = initial_rows - len(df)
    if dedup_count > 0:
        logger.info(f"Removed {dedup_count} duplicate run_id records")
    
    return df


def transform_qc_metrics(qc_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform QC metrics table:
    - Normalize strings
    - Type casting
    - Boolean normalization
    """
    logger.info("Transforming qc_metrics table")
    
    df = qc_df.copy()
    
    # Normalize string columns
    df["run_id"] = normalize_string_column(df["run_id"])
    
    # Numeric casting
    df["total_reads"] = cast_numeric(df["total_reads"], dtype="int64")
    df["q30_rate"] = cast_numeric(df["q30_rate"], dtype="float64")
    df["gc_percent"] = cast_numeric(df["gc_percent"], dtype="float64")
    df["duplication_rate"] = cast_numeric(df["duplication_rate"], dtype="float64")
    
    # Boolean normalization
    if "adapter_content_flag" in df.columns:
        df["adapter_content_flag"] = (
            df["adapter_content_flag"]
            .astype(str)
            .str.lower()
            .isin(["true", "1", "yes"])
        )
    
    return df


def transform_all(
    samples_df: pd.DataFrame,
    runs_df: pd.DataFrame,
    qc_df: pd.DataFrame,
) -> Dict[str, pd.DataFrame]:
    """Apply all transformations."""
    return {
        "samples": transform_samples(samples_df),
        "runs": transform_runs(runs_df),
        "qc_metrics": transform_qc_metrics(qc_df),
    }
