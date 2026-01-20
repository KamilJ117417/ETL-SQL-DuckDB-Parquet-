#!/usr/bin/env python3
"""Quick test to validate ETL pipeline locally."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, '/workspaces/ETL-SQL-DuckDB-Parquet-')

import pandas as pd
from src.etl.ingest import ingest_all
from src.etl.validate import validate_all
from src.etl.transform import transform_all
from src.etl.settings import ETLMode

def test_etl():
    """Run quick ETL test."""
    print("=== Testing ETL Pipeline ===\n")
    
    # Test ingest
    print("1. INGEST")
    raw_dir = Path('/workspaces/ETL-SQL-DuckDB-Parquet-/data/raw')
    dfs = ingest_all(raw_dir)
    
    print(f"  ✓ Ingested {len(dfs)} tables:")
    for name, df in dfs.items():
        print(f"    - {name}: {len(df)} rows")
    
    # Test validate
    print("\n2. VALIDATE")
    is_valid, errors = validate_all(dfs['samples'], dfs['runs'], dfs['qc_metrics'], mode=ETLMode.STRICT)
    print(f"  ✓ Validation {'PASSED' if is_valid else 'FAILED'}")
    if errors:
        print(f"    - Found {len(errors)} errors")
        for err in errors[:3]:
            print(f"      {err}")
    
    # Test transform
    print("\n3. TRANSFORM")
    transformed = transform_all(dfs['samples'], dfs['runs'], dfs['qc_metrics'])
    print(f"  ✓ Transformed data:")
    for name, df in transformed.items():
        print(f"    - {name}: {len(df)} rows, {len(df.columns)} columns")
    
    print("\n✓ ETL pipeline test completed successfully!")

if __name__ == '__main__':
    try:
        test_etl()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
