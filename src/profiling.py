"""Data Profiling Module - Generate data quality statistics and analysis."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def get_column_stats(series: pd.Series) -> Dict[str, Any]:
    """Get comprehensive statistics for a column."""
    dtype = series.dtype
    stats = {
        "name": series.name,
        "dtype": str(dtype),
        "count": len(series),
        "nulls": series.isnull().sum(),
        "unique": series.nunique(),
    }
    
    # Numeric stats
    if np.issubdtype(dtype, np.number):
        stats.update({
            "min": float(series.min()),
            "max": float(series.max()),
            "mean": float(series.mean()),
            "std": float(series.std()),
            "median": float(series.median()),
        })
    
    # String stats
    elif dtype == "object":
        stats.update({
            "max_length": series.astype(str).str.len().max(),
            "min_length": series.astype(str).str.len().min(),
        })
    
    stats["completeness"] = (1 - stats["nulls"] / stats["count"]) * 100
    
    return stats


def profile_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate comprehensive profile for entire dataframe."""
    logger.info(f"Profiling dataframe with {len(df)} rows and {len(df.columns)} columns")
    
    profile = {
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "memory_mb": df.memory_usage(deep=True).sum() / (1024 * 1024),
        "columns": {},
        "correlations": {},
        "duplicates": df.duplicated().sum(),
    }
    
    # Column stats
    for col in df.columns:
        profile["columns"][col] = get_column_stats(df[col])
    
    # Correlations (numeric only)
    numeric_df = df.select_dtypes(include=[np.number])
    if len(numeric_df.columns) > 1:
        profile["correlations"] = numeric_df.corr().to_dict()
    
    return profile


def detect_outliers(series: pd.Series, method: str = "iqr") -> List[int]:
    """Detect outliers using IQR or z-score method."""
    if method == "iqr":
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        outliers = series[(series < Q1 - 1.5 * IQR) | (series > Q3 + 1.5 * IQR)].index.tolist()
    else:  # z-score
        from scipy import stats
        z_scores = np.abs(stats.zscore(series.dropna()))
        outliers = series[z_scores > 3].index.tolist()
    
    return outliers


def data_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate data quality report."""
    report = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "total_cells": len(df) * len(df.columns),
        "missing_cells": df.isnull().sum().sum(),
        "duplicate_rows": df.duplicated().sum(),
        "column_quality": {}
    }
    
    for col in df.columns:
        completeness = (1 - df[col].isnull().sum() / len(df)) * 100
        report["column_quality"][col] = {
            "completeness": round(completeness, 2),
            "missing": df[col].isnull().sum(),
            "unique": df[col].nunique(),
        }
    
    # Overall quality score
    missing_rate = report["missing_cells"] / report["total_cells"] * 100
    dup_rate = report["duplicate_rows"] / report["total_rows"] * 100
    quality_score = 100 - (missing_rate + dup_rate)
    report["quality_score"] = max(0, min(100, quality_score))
    
    return report


def compare_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, label1: str = "Before", label2: str = "After") -> Dict[str, Any]:
    """Compare two dataframes and generate diff report."""
    comparison = {
        label1: {
            "rows": len(df1),
            "columns": len(df1.columns),
            "memory_mb": df1.memory_usage(deep=True).sum() / (1024 * 1024),
            "nulls": df1.isnull().sum().sum(),
        },
        label2: {
            "rows": len(df2),
            "columns": len(df2.columns),
            "memory_mb": df2.memory_usage(deep=True).sum() / (1024 * 1024),
            "nulls": df2.isnull().sum().sum(),
        },
        "changes": {
            "rows_added": len(df2) - len(df1),
            "rows_removed": len(df1) - len(df2),
            "memory_saved_mb": (df1.memory_usage(deep=True).sum() - df2.memory_usage(deep=True).sum()) / (1024 * 1024),
        }
    }
    
    return comparison
