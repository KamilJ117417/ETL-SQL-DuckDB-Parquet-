# Benchmark Module Fixes

## Issues Fixed

### 1. ❌ Wrong Column Names
**Problem:** Query searched for `q30_rate` column in `runs.csv`, but this column only exists in `qc_metrics.tsv`
```
ERROR: Referenced column "q30_rate" not found in FROM clause!
```

**Solution:** Changed benchmark query to use columns that actually exist in `runs.csv`:
- Old: `SELECT run_id, q30_rate FROM data ORDER BY q30_rate ASC LIMIT 10`
- New: `SELECT run_id, read_length FROM data ORDER BY read_length DESC LIMIT 10`

### 2. ❌ Division by Zero
**Problem:** When Parquet file doesn't exist, `parquet_size = 0`, causing crash:
```python
Compression Ratio | {csv_size / parquet_size:.1f}× |
                     ~~~~~~~~~^~~~~~~~~~~~~~
ZeroDivisionError: float division by zero
```

**Solution:** Added safety check:
```python
compression_text = f"{csv_size / parquet_size:.1f}×" if parquet_size > 0 else "N/A (Parquet not yet created)"
```

### 3. ❌ Missing Parquet File Handling
**Problem:** Code tried to benchmark Parquet queries even when file didn't exist, causing cascading errors

**Solution:** Added `parquet_exists` check:
```python
parquet_exists = parquet_file.exists()
if parquet_exists:
    # Only run parquet benchmarks if file actually exists
    for i in range(iterations):
        # ...
```

### 4. ❌ None Values in Report
**Problem:** When Parquet benchmarks were skipped, code tried to format `None` values:
```python
| {r['speedup']:.1f}× |  # Crashes if speedup is None
```

**Solution:** Added null checks when generating report:
```python
parquet_time_text = f"{r['parquet_time_ms']:.1f}" if r['parquet_time_ms'] is not None else "N/A"
speedup_text = f"{r['speedup']:.1f}×" if r['speedup'] is not None else "N/A"
```

## Modified Functions

### `benchmark_query()`
- Added `parquet_exists` check
- Returns `None` for parquet metrics if file doesn't exist
- Safe speedup calculation

### `run_benchmark()`
- Fixed compression ratio calculation with fallback
- Updated queries to use valid columns
- Safe formatting of report values

## How to Use

### Option 1: After running full ETL pipeline
```bash
python -m src.cli etl --mode strict
python -m src.cli benchmark --csv-file data/raw/runs.csv --parquet-file data/processed/fact_runs.parquet
```

### Option 2: Direct Python execution
```python
from pathlib import Path
from src.benchmarks import run_benchmark

result = run_benchmark(
    Path('data/raw/runs.csv'),
    Path('data/processed/fact_runs.parquet')
)
print(result)
```

## Expected Output

When Parquet file doesn't exist yet:
```
## File Sizes

| Format | Size (MB) |
|--------|-----------|
| CSV | 0.00 |
| Parquet | 0.00 |
| Compression Ratio | N/A (Parquet not yet created) |

## Query Performance (median of 3 runs)

| Query | CSV (ms) | Parquet (ms) | Speedup |
|-------|----------|--------------|---------|
| Longest read length | 5.2 | N/A | N/A |
| Sum FASTQ per run | 3.1 | N/A | N/A |
```

After running ETL:
```
| Compression Ratio | 8.2× |
| Longest read length | 5.2 | 0.8 | 6.5× |
| Sum FASTQ per run | 3.1 | 0.6 | 5.2× |
```

## Testing

To verify the fixes work:
```bash
# Just CSV benchmarks (no Parquet file needed)
python -c "
from pathlib import Path
from src.benchmarks import run_benchmark
result = run_benchmark(Path('data/raw/runs.csv'), Path('data/processed/nonexistent.parquet'))
print(result)
"
```

✅ Should run without errors and show CSV timings with "N/A" for Parquet metrics.
