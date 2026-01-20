#!/usr/bin/env python3
import os
import zipfile
from pathlib import Path

# Change working dir
os.chdir('/workspaces/ETL-SQL-DuckDB-Parquet-')

zip_file = 'data/raw/genomics-metadata-etl-duckdb-example-data.zip'
extract_dir = 'data/raw/example_data'

print(f"Current dir: {os.getcwd()}")
print(f"ZIP file exists: {Path(zip_file).exists()}")
print(f"ZIP file size: {Path(zip_file).stat().st_size if Path(zip_file).exists() else 'N/A'} bytes")

# Extract
if Path(zip_file).exists():
    Path(extract_dir).mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_file, 'r') as zf:
        zf.extractall(extract_dir)
        print(f"\n✓ Extracted to: {extract_dir}")
        print(f"Files extracted:")
        for item in sorted(zf.namelist()):
            if not item.startswith('__MACOSX'):
                print(f"  - {item}")
else:
    print(f"ZIP file not found at {zip_file}")
