"""Schema Inspector Module - Analyze and manage data schemas."""

import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def inspect_parquet_schema(parquet_path: Path) -> Dict[str, Any]:
    """Inspect Parquet file schema."""
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    
    parquet_file = pq.ParquetFile(parquet_path)
    schema = parquet_file.schema
    
    schema_info = {
        "file": str(parquet_path),
        "num_rows": parquet_file.metadata.num_rows,
        "num_columns": len(schema),
        "file_size_mb": parquet_file.metadata.serialized_size / (1024 * 1024),
        "columns": {}
    }
    
    for i, field in enumerate(schema):
        col_name = field.name
        col_type = str(field.type)
        
        # Get column statistics
        col_chunk_meta = parquet_file.metadata.row_group(0).column(i)
        
        schema_info["columns"][col_name] = {
            "type": col_type,
            "nullable": field.nullable,
            "index": i,
        }
    
    return schema_info


def inspect_csv_schema(csv_path: Path) -> Dict[str, Any]:
    """Inspect CSV file schema."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path, nrows=1000)
    
    schema_info = {
        "file": str(csv_path),
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "file_size_mb": csv_path.stat().st_size / (1024 * 1024),
        "columns": {}
    }
    
    for i, col in enumerate(df.columns):
        schema_info["columns"][col] = {
            "type": str(df[col].dtype),
            "nullable": df[col].isnull().any(),
            "index": i,
            "null_count": df[col].isnull().sum(),
        }
    
    return schema_info


def compare_schemas(schema1: Dict[str, Any], schema2: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two schemas."""
    cols1 = set(schema1.get("columns", {}).keys())
    cols2 = set(schema2.get("columns", {}).keys())
    
    comparison = {
        "source": schema1.get("file", "Unknown"),
        "target": schema2.get("file", "Unknown"),
        "common_columns": list(cols1 & cols2),
        "missing_in_target": list(cols1 - cols2),
        "new_in_target": list(cols2 - cols1),
        "type_changes": {},
        "row_difference": schema2.get("num_rows", 0) - schema1.get("num_rows", 0),
    }
    
    # Check type changes
    for col in comparison["common_columns"]:
        type1 = schema1["columns"][col].get("type")
        type2 = schema2["columns"][col].get("type")
        if type1 != type2:
            comparison["type_changes"][col] = {
                "from": type1,
                "to": type2
            }
    
    return comparison


def get_column_mappings(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Get detailed column mappings for a dataframe."""
    mappings = {}
    
    for col in df.columns:
        dtype = df[col].dtype
        
        mappings[col] = {
            "name": col,
            "type": str(dtype),
            "null_count": df[col].isnull().sum(),
            "null_percentage": (df[col].isnull().sum() / len(df)) * 100,
            "unique_count": df[col].nunique(),
            "sample_values": df[col].dropna().head(3).tolist() if len(df) > 0 else [],
        }
        
        # Add numeric stats
        if pd.api.types.is_numeric_dtype(df[col]):
            mappings[col].update({
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "mean": float(df[col].mean()),
            })
    
    return mappings


def validate_schema_compatibility(csv_schema: Dict, parquet_schema: Dict) -> Dict[str, Any]:
    """Validate if schemas are compatible."""
    validation = {
        "is_compatible": True,
        "warnings": [],
        "errors": []
    }
    
    csv_cols = set(csv_schema.get("columns", {}).keys())
    parquet_cols = set(parquet_schema.get("columns", {}).keys())
    
    # Check for missing columns
    missing = csv_cols - parquet_cols
    if missing:
        validation["errors"].append(f"Columns in CSV but not in Parquet: {missing}")
        validation["is_compatible"] = False
    
    extra = parquet_cols - csv_cols
    if extra:
        validation["warnings"].append(f"Extra columns in Parquet: {extra}")
    
    # Check row differences
    row_diff = abs(parquet_schema.get("num_rows", 0) - csv_schema.get("num_rows", 0))
    if row_diff > 0:
        validation["warnings"].append(f"Row count difference: {row_diff}")
    
    return validation


def generate_schema_report(parquet_dir: Path) -> Dict[str, Any]:
    """Generate comprehensive schema report for all Parquet files."""
    report = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "parquet_dir": str(parquet_dir),
        "files": {}
    }
    
    for parquet_file in parquet_dir.glob("*.parquet"):
        try:
            schema = inspect_parquet_schema(parquet_file)
            report["files"][parquet_file.name] = schema
        except Exception as e:
            logger.error(f"Error inspecting {parquet_file}: {str(e)}")
    
    return report


def export_schema_as_csv(schema: Dict[str, Any], output_path: Path) -> str:
    """Export schema definition to CSV."""
    rows = []
    
    for col_name, col_info in schema.get("columns", {}).items():
        rows.append({
            "Column Name": col_name,
            "Data Type": col_info.get("type"),
            "Nullable": col_info.get("nullable", False),
            "Index": col_info.get("index")
        })
    
    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Schema exported to {output_path}")
    return str(output_path)
