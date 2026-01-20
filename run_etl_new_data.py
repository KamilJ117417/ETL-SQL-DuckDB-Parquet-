#!/usr/bin/env python3
"""Run ETL pipeline on new dataset"""
import sys
from pathlib import Path

# Set working directory
import os
os.chdir('/workspaces/ETL-SQL-DuckDB-Parquet-')
sys.path.insert(0, str(Path.cwd()))

from src.etl.ingest import ingest_all
from src.etl.validate import validate_all
from src.etl.transform import transform_all
from src.etl.load import load_to_processed
from src.etl.settings import ETLMode
import pandas as pd

print("=" * 70)
print("🚀 RUNNING ETL PIPELINE ON NEW DATASET")
print("=" * 70)

try:
    # INGEST
    print("\n1️⃣ INGESTING raw data...")
    dfs = ingest_all(Path('data/raw'))
    print(f"   ✓ Samples: {len(dfs['samples'])} rows")
    print(f"   ✓ Runs: {len(dfs['runs'])} rows")
    print(f"   ✓ QC Metrics: {len(dfs['qc_metrics'])} rows")

    # VALIDATE
    print("\n2️⃣ VALIDATING data...")
    is_valid, errors = validate_all(
        dfs['samples'],
        dfs['runs'],
        dfs['qc_metrics'],
        mode=ETLMode.STRICT
    )

    if is_valid:
        print(f"   ✓ Validation PASSED")
    else:
        print(f"   ❌ Validation FAILED: {len(errors)} errors")
        for err in errors[:5]:
            print(f"      - {err}")
        sys.exit(1)

    # TRANSFORM
    print("\n3️⃣ TRANSFORMING data...")
    transformed = transform_all(
        dfs['samples'],
        dfs['runs'],
        dfs['qc_metrics']
    )
    print(f"   ✓ Samples: {len(transformed['samples'])} rows transformed")
    print(f"   ✓ Runs: {len(transformed['runs'])} rows transformed")
    print(f"   ✓ QC Metrics: {len(transformed['qc_metrics'])} rows transformed")

    # LOAD
    print("\n4️⃣ LOADING to Parquet...")
    load_to_processed(
        transformed['samples'],
        transformed['runs'],
        transformed['qc_metrics'],
        Path('data/processed')
    )

    # Check files created
    processed_dir = Path('data/processed')
    if processed_dir.exists():
        print("   ✓ Files created:")
        for f in sorted(processed_dir.glob('*.parquet')):
            size_mb = f.stat().st_size / (1024*1024)
            print(f"      - {f.name:<35} {size_mb:>8.2f} MB")

    # SUMMARY
    print("\n" + "=" * 70)
    print("📊 ETL SUMMARY")
    print("=" * 70)

    print(f"\n✅ Pipeline completed successfully!")
    print(f"\n📈 Data sizes:")
    print(f"   Samples (raw):        {len(dfs['samples']):>4} → {len(transformed['samples']):>4} (transformed)")
    print(f"   Runs (raw):           {len(dfs['runs']):>4} → {len(transformed['runs']):>4} (transformed)")
    print(f"   QC Metrics (raw):     {len(dfs['qc_metrics']):>4} → {len(transformed['qc_metrics']):>4} (transformed)")

    print(f"\n📁 New columns in data:")
    print(f"   Samples: {', '.join(transformed['samples'].columns.tolist())}")
    print(f"   Runs: {', '.join(transformed['runs'].columns.tolist())}")

    print("\n🎯 Next steps:")
    print("   1. Run queries: python -m src.cli query --sql 'SELECT COUNT(*) FROM samples'")
    print("   2. Benchmark: python -m src.cli benchmark --csv-file data/raw/runs.csv --parquet-file data/processed/fact_runs.parquet")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
