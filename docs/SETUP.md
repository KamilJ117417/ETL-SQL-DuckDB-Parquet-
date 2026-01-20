# Development Guide

This document provides detailed instructions for developing, testing, and extending the genomics metadata ETL pipeline.

## Quick Start (5 minutes)

```bash
# 1. Clone and setup
git clone https://github.com/yourusername/genomics-metadata-etl-duckdb.git
cd genomics-metadata-etl-duckdb
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install dev dependencies
pip install -e ".[dev]"

# 3. Run tests
pytest tests/ -v

# 4. Run ETL
python -m src.cli etl --input data/raw --output data/processed --mode strict

# 5. Run queries
python -m src.cli query --parquet data/processed --sql sql/queries.sql

# 6. Benchmark
python -m src.cli benchmark --csv data/raw/runs.csv --parquet data/processed/fact_runs.parquet
```

## Project Structure

### `/src/etl/` — ETL Modules

- **settings.py** — Enums, constants, validation rules
- **ingest.py** — CSV/TSV reader with auto-detection
- **validate.py** — Data quality checks, FK constraints
- **transform.py** — Type casting, normalization, dedup
- **load.py** — Parquet writer with partitioning

### `/sql/` — SQL Code

- **schema.sql** — DuckDB views over Parquet
- **queries.sql** — 12 analytic queries
- **views.sql** — (optional) materialized views

### `/data/` — Data

- **raw/** — Input CSV/TSV (small examples, >1K rows ignored)
- **processed/** — Output Parquet (gitignored)
- **staging/** — Temporary files (gitignored)
- **quarantine/** — Validation errors (gitignored)

### `/docs/` — Documentation

- **data_dictionary.md** — Column definitions, relationships
- **example_queries.md** — 12 detailed query examples
- **benchmark_results.md** — Performance analysis

### `/tests/` — Tests

- **test_validate.py** — Validation tests (8+ test cases)
- **test_transform.py** — Transform tests (8+ test cases)
- **data/** — Small fixtures for testing

## Development Workflow

### 1. Add a New Validation Rule

File: `src/etl/validate.py`

```python
def validate_my_new_rule(df: pd.DataFrame) -> ValidationResult:
    """Check my business rule."""
    errors = []
    
    # Example: check if column_x > 0
    invalid = df[df['column_x'] <= 0].index.tolist()
    if invalid:
        for idx in invalid:
            errors.append(ValidationError(
                idx, 'column_x', df.loc[idx, 'column_x'], 'RANGE',
                f'column_x must be > 0 at row {idx}'
            ))
    
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

Then add to `validate_all()`:

```python
result = validate_my_new_rule(df)
if not result.is_valid:
    all_errors.extend(result.errors)
```

### 2. Add a New SQL Query

File: `sql/queries.sql`

```sql
-- Q13: My new query
SELECT
  s.project_id,
  COUNT(DISTINCT r.run_id) as n_runs
FROM samples s
LEFT JOIN runs r USING(sample_id)
GROUP BY 1
ORDER BY n_runs DESC;
```

Run:
```bash
python -m src.cli query --parquet data/processed --sql sql/queries.sql --output docs/results.md
```

### 3. Add a New Command to CLI

File: `src/cli.py`

```python
@app.command()
def my_command(
    input_file: Path = typer.Option("data/raw/file.csv", help="Input file"),
    output_file: Path = typer.Option("output.txt", help="Output file"),
) -> None:
    """Description of my command."""
    logger.info("Running my command")
    try:
        # Your logic here
        pass
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        sys.exit(1)
```

Run:
```bash
python -m src.cli my-command --input-file data.csv --output-file result.txt
```

## Testing

### Run All Tests

```bash
pytest tests/ -v --cov=src
```

### Run Specific Test

```bash
pytest tests/test_validate.py::TestValidateSamples::test_null_sample_id -v
```

### Write a New Test

File: `tests/test_my_module.py`

```python
import pytest
import pandas as pd
from src.my_module import my_function

class TestMyFunction:
    def test_basic_case(self):
        """Test description."""
        input_data = pd.DataFrame({...})
        result = my_function(input_data)
        assert result.is_valid
```

Run:
```bash
pytest tests/test_my_module.py -v
```

## Linting & Formatting

```bash
# Check code quality
ruff check src/ tests/

# Format code
black src/ tests/

# Type checking
mypy src/ --ignore-missing-imports

# One-liner: lint + format + test
ruff check --fix src/ && black src/ && pytest tests/
```

## Debugging

### Enable Debug Logging

```bash
python -m src.cli etl --input data/raw --output data/processed --log-level DEBUG
```

### Debug a Specific Module

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from src.etl.ingest import ingest_all
dfs = ingest_all(Path('data/raw'))
```

### Inspect Parquet Files

```python
import pyarrow.parquet as pq

# Read metadata
parquet_file = pq.ParquetFile('data/processed/dim_samples.parquet')
print(parquet_file.schema)
print(parquet_file.metadata)

# Read data
table = parquet_file.read()
print(table.to_pandas())
```

## Performance Tuning

### Benchmark a Query

```bash
python -m src.cli benchmark \
  --csv data/raw/runs.csv \
  --parquet data/processed/fact_runs.parquet \
  --output docs/benchmark_results.md
```

### Profile ETL

```python
import cProfile
import pstats
from src.etl.ingest import ingest_all

pr = cProfile.Profile()
pr.enable()

dfs = ingest_all(Path('data/raw'))

pr.disable()
stats = pstats.Stats(pr)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Query Statistics (DuckDB)

```python
import duckdb

conn = duckdb.connect(':memory:')
result = conn.execute("""
  EXPLAIN SELECT * FROM read_parquet('data/processed/dim_samples.parquet')
  WHERE project_id = 'PRJNA001000'
""").fetchall()
for row in result:
    print(row)
```

## Continuous Integration

Push to GitHub to trigger `.github/workflows/ci.yml`:

1. **pytest** — Run all tests
2. **ruff** — Lint code
3. **black** — Check formatting
4. **mypy** — Type checking

Failure on any step blocks merge.

## Extending with S3

### Push to S3

```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
export S3_BUCKET=my-bucket

python -m src.cli s3-push-cmd --local-dir data/processed --prefix genomics/curated/
```

### Pull from S3

```bash
python -m src.cli s3-pull-cmd --prefix genomics/curated/ --local-dir data/s3_download/
```

### Query S3 Directly

```python
import duckdb

conn = duckdb.connect(':memory:')

# Requires httpfs extension (DuckDB 0.8+)
result = conn.execute("""
  SELECT * FROM read_parquet('s3://my-bucket/genomics/curated/dim_samples.parquet')
  WHERE project_id = 'PRJNA001000'
""").fetchall()

print(result)
```

## Common Issues

### Q: Tests fail with "ModuleNotFoundError"

A: Install in editable mode:
```bash
pip install -e .
```

### Q: Parquet file too large

A: Add partitioning by project_id:
```bash
python -m src.cli etl --partition-cols project_id,platform
```

### Q: DuckDB queries are slow

A: Check if Parquet is being read efficiently:
```python
import duckdb
conn = duckdb.connect(':memory:')
conn.execute("PRAGMA explain_output='physical'")
conn.execute("EXPLAIN SELECT COUNT(*) FROM read_parquet('...')").fetchall()
```

### Q: S3 authentication fails

A: Check IAM credentials:
```bash
aws sts get-caller-identity  # Should work
aws s3 ls s3://my-bucket/    # Should list files
```

## Contributing Guidelines

1. **Fork** the repo
2. **Create branch**: `git checkout -b feature/my-feature`
3. **Write tests** for new functionality
4. **Pass CI**: All checks must pass
5. **Write docs**: Update README, data_dictionary.md, etc.
6. **Submit PR** with clear description

## Release Checklist

- [ ] All tests pass locally
- [ ] CI passes on GitHub
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG.md updated
- [ ] README updated
- [ ] Tag commit: `git tag v0.2.0`
- [ ] Push tags: `git push --tags`
- [ ] Build package: `python -m build`
- [ ] Publish to PyPI: `twine upload dist/*`

## References

- [DuckDB Docs](https://duckdb.org/docs/)
- [Apache Parquet](https://parquet.apache.org/docs/)
- [Pandas API](https://pandas.pydata.org/docs/)
- [PyArrow](https://arrow.apache.org/docs/python/)
- [Typer CLI](https://typer.tiangolo.com/)
- [pytest](https://docs.pytest.org/)
