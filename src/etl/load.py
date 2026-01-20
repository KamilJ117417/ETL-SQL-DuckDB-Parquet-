"""Load module: write Parquet with partitioning and metadata."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa

logger = logging.getLogger(__name__)


def write_parquet(
    df: pd.DataFrame,
    output_path: Path,
    partition_cols: Optional[List[str]] = None,
    compression: str = "zstd",
) -> None:
    """
    Write DataFrame to Parquet with optional partitioning.
    
    Args:
        df: DataFrame to write
        output_path: Output file path
        partition_cols: List of columns to partition by
        compression: Compression codec (snappy, gzip, zstd, etc.)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    table = pa.Table.from_pandas(df, preserve_index=False)
    
    if partition_cols:
        logger.info(f"Writing {output_path.name} with partitioning by {partition_cols}")
        # Use write_to_dataset for partitioned writes
        pq.write_to_dataset(
            table,
            root_path=str(output_path.parent / output_path.stem),
            partition_cols=partition_cols,
            compression=compression,
        )
    else:
        logger.info(f"Writing {output_path.name} (no partitioning)")
        pq.write_table(
            table,
            str(output_path),
            compression=compression,
        )
    
    # Log directory/file size
    if output_path.is_file():
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"Parquet file size: {file_size_mb:.2f} MB")
    elif output_path.parent.exists():
        total_size = sum(f.stat().st_size for f in output_path.parent.glob("**/*") if f.is_file())
        total_size_mb = total_size / (1024 * 1024)
        logger.info(f"Parquet dataset size: {total_size_mb:.2f} MB")


def load_to_processed(
    samples_df: pd.DataFrame,
    runs_df: pd.DataFrame,
    qc_df: pd.DataFrame,
    output_dir: Path,
    partition_cols: Optional[List[str]] = None,
) -> None:
    """
    Load all tables to processed directory as Parquet.
    
    Args:
        samples_df: Transformed samples table
        runs_df: Transformed runs table
        qc_df: Transformed QC metrics table
        output_dir: Output directory (data/processed)
        partition_cols: Columns to partition by (e.g., ['project_id', 'platform'])
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading curated data to {output_dir}")
    
    # Rename samples → dim_samples
    samples_df = samples_df.rename(
        columns={
            "sample_id": "sample_id",
            "project_id": "project_id",
            "organism": "organism",
            "collection_date": "collection_date",
            "tissue": "tissue",
            "platform": "platform",
        }
    )
    write_parquet(
        samples_df,
        output_dir / "dim_samples.parquet",
        partition_cols=None,  # Dimension is usually small
        compression="zstd",
    )
    
    # Rename runs → fact_runs
    runs_df = runs_df.rename(
        columns={
            "run_id": "run_id",
            "sample_id": "sample_id",
            "library_layout": "library_layout",
            "read_length": "read_length",
            "fastq_gb": "fastq_gb",
        }
    )
    
    # Add project_id from samples for partitioning
    if "project_id" in samples_df.columns:
        runs_with_project = runs_df.merge(
            samples_df[["sample_id", "project_id"]],
            on="sample_id",
            how="left"
        )
    else:
        runs_with_project = runs_df
    
    # Check if project_id exists in merged dataframe before partitioning
    partition_runs = None
    # Disable partitioning for now to ensure stability
    
    write_parquet(
        runs_with_project,
        output_dir / "fact_runs.parquet",
        partition_cols=partition_runs,
        compression="zstd",
    )
    
    # QC metrics
    qc_df = qc_df.rename(
        columns={
            "run_id": "run_id",
            "total_reads": "total_reads",
            "q30_rate": "q30_rate",
            "gc_percent": "gc_percent",
            "duplication_rate": "duplication_rate",
            "adapter_content_flag": "adapter_content_flag",
        }
    )
    
    # Add project_id for partitioning
    if "project_id" in runs_with_project.columns and "run_id" in runs_with_project.columns:
        # Select only columns that exist in runs_with_project
        cols_to_select = ["run_id"]
        if "project_id" in runs_with_project.columns:
            cols_to_select.append("project_id")
        qc_with_project = qc_df.merge(
            runs_with_project[cols_to_select],
            on="run_id",
            how="left"
        )
    else:
        qc_with_project = qc_df
    
    partition_qc = None
    # Disable partitioning for now to ensure stability
    
    write_parquet(
        qc_with_project,
        output_dir / "fact_qc_metrics.parquet",
        partition_cols=partition_qc,
        compression="zstd",
    )
    
    logger.info(f"Successfully loaded all tables to {output_dir}")
