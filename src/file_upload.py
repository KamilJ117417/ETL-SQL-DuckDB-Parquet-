"""File Upload and Batch Processing Module."""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging
import tempfile

logger = logging.getLogger(__name__)


def validate_file(file_path: Path) -> Tuple[bool, str]:
    """Validate if file is in correct format."""
    valid_extensions = {".csv", ".tsv", ".txt"}
    
    if file_path.suffix.lower() not in valid_extensions:
        return False, f"Invalid file type: {file_path.suffix}. Expected: {valid_extensions}"
    
    try:
        # Try to read file
        if file_path.suffix.lower() == ".tsv":
            pd.read_csv(file_path, sep="\t", nrows=1)
        else:
            pd.read_csv(file_path, nrows=1)
        return True, "Valid"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def process_uploaded_file(
    uploaded_file,
    target_dir: Path,
    file_type: str = "samples"  # samples, runs, qc_metrics
) -> Tuple[bool, str, Dict[str, Any]]:
    """Process an uploaded file."""
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Save uploaded file
        file_path = target_dir / uploaded_file.name
        
        # Handle streamlit UploadedFile or regular file
        if hasattr(uploaded_file, 'getvalue'):
            # Streamlit UploadedFile
            content = uploaded_file.getvalue()
            with open(file_path, 'wb') as f:
                f.write(content)
        else:
            # Regular file
            with open(file_path, 'rb') as src:
                with open(target_dir / uploaded_file.name, 'wb') as dst:
                    dst.write(src.read())
        
        # Validate file
        is_valid, message = validate_file(file_path)
        if not is_valid:
            return False, message, {}
        
        # Read and analyze
        if file_path.suffix.lower() == ".tsv":
            df = pd.read_csv(file_path, sep="\t")
        else:
            df = pd.read_csv(file_path)
        
        info = {
            "file_name": uploaded_file.name,
            "file_path": str(file_path),
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "file_size_mb": file_path.stat().st_size / (1024 * 1024),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "preview": df.head(5).to_dict('records')
        }
        
        logger.info(f"File uploaded: {uploaded_file.name} ({len(df)} rows)")
        return True, "File uploaded successfully", info
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return False, f"Error: {str(e)}", {}


def batch_process_files(
    file_list: List[Path],
    process_func,
    target_dir: Path
) -> Dict[str, Any]:
    """Process multiple files in batch."""
    
    results = {
        "total": len(file_list),
        "successful": 0,
        "failed": 0,
        "files": []
    }
    
    for file_path in file_list:
        try:
            logger.info(f"Processing {file_path.name}...")
            
            # Validate
            is_valid, message = validate_file(file_path)
            if not is_valid:
                results["files"].append({
                    "file": file_path.name,
                    "status": "failed",
                    "reason": message
                })
                results["failed"] += 1
                continue
            
            # Process
            result = process_func(file_path, target_dir)
            
            results["files"].append({
                "file": file_path.name,
                "status": "success",
                "result": result
            })
            results["successful"] += 1
            
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {str(e)}")
            results["files"].append({
                "file": file_path.name,
                "status": "failed",
                "reason": str(e)
            })
            results["failed"] += 1
    
    return results


def merge_files(
    file_list: List[Path],
    output_path: Path,
    file_type: str = "csv"
) -> Tuple[bool, str]:
    """Merge multiple files into one."""
    
    try:
        dfs = []
        
        for file_path in file_list:
            if file_path.suffix.lower() == ".tsv":
                df = pd.read_csv(file_path, sep="\t")
            else:
                df = pd.read_csv(file_path)
            dfs.append(df)
        
        # Merge
        merged_df = pd.concat(dfs, ignore_index=True)
        
        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if file_type == "tsv":
            merged_df.to_csv(output_path, sep="\t", index=False)
        else:
            merged_df.to_csv(output_path, index=False)
        
        logger.info(f"Files merged: {len(file_list)} files → {len(merged_df)} rows")
        return True, f"Merged {len(file_list)} files with {len(merged_df)} total rows"
        
    except Exception as e:
        logger.error(f"Error merging files: {str(e)}")
        return False, f"Error: {str(e)}"


def get_file_stats(file_path: Path) -> Dict[str, Any]:
    """Get statistics for a file."""
    
    if file_path.suffix.lower() == ".tsv":
        df = pd.read_csv(file_path, sep="\t")
    else:
        df = pd.read_csv(file_path)
    
    return {
        "file_name": file_path.name,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "file_size_mb": file_path.stat().st_size / (1024 * 1024),
        "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024),
        "null_counts": df.isnull().sum().to_dict(),
        "dtypes": df.dtypes.to_dict()
    }
