"""Ingest module: read CSV/TSV and add audit columns."""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def detect_separator(file_path: Path, encoding: str = "utf-8") -> str:
    """Detect CSV/TSV separator."""
    with open(file_path, encoding=encoding) as f:
        header = f.readline().strip()
    
    # Count occurrences of common separators in the header
    separators = {",": header.count(","), "\t": header.count("\t"), ";": header.count(";")}
    return max(separators, key=separators.get)  # Return most common


def ingest_file(
    file_path: Path,
    source_name: str,
    encoding: str = "utf-8",
    separator: Optional[str] = None,
) -> pd.DataFrame:
    """
    Read CSV/TSV file and add audit columns.
    
    Args:
        file_path: Path to input file
        source_name: Logical name (e.g., 'samples', 'runs', 'qc_metrics')
        encoding: File encoding (default: utf-8)
        separator: Override separator detection (None = auto-detect)
    
    Returns:
        DataFrame with canonical column names and audit columns
    """
    if separator is None:
        separator = detect_separator(file_path, encoding)
    
    logger.info(f"Ingesting {source_name} from {file_path} (separator='{repr(separator)}')")
    
    df = pd.read_csv(file_path, sep=separator, encoding=encoding, dtype=str)
    
    # Normalize column names: lowercase and strip
    df.columns = df.columns.str.lower().str.strip()
    
    # Add audit columns
    now = datetime.utcnow().isoformat()
    df["ingested_at"] = now
    df["source_file"] = file_path.name
    df["row_hash"] = df.apply(
        lambda row: hashlib.sha256(row.to_string().encode()).hexdigest(), axis=1
    )
    
    logger.info(f"Ingested {len(df)} rows from {source_name}")
    return df


def ingest_all(raw_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Ingest all files from raw directory.
    
    Expected files:
    - samples.csv
    - runs.csv
    - qc_metrics.tsv
    """
    dfs = {}
    
    files_spec = [
        (raw_dir / "samples.csv", "samples"),
        (raw_dir / "runs.csv", "runs"),
        (raw_dir / "qc_metrics.tsv", "qc_metrics"),
    ]
    
    for file_path, name in files_spec:
        if file_path.exists():
            dfs[name] = ingest_file(file_path, name)
        else:
            logger.warning(f"File not found: {file_path}")
    
    return dfs
