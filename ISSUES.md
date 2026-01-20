# Issue Pack: Implementation Roadmap

This issue pack provides a structured roadmap for building the genomics metadata ETL pipeline. Each issue represents a complete, testable increment of work.

## Issue #1: Initialize Repository & CI

**Title**: Set up project structure, README, CI pipeline

**Description**:
- Create directory structure (src/, tests/, data/, sql/, docs/)
- Write comprehensive README with quick start
- Set up pyproject.toml with dependencies
- Create GitHub Actions CI workflow (.github/workflows/ci.yml)
- Add .gitignore, .env.example

**Acceptance Criteria**:
- ✓ README builds clear mental model
- ✓ CI passes on main branch
- ✓ `pip install -e .` works
- ✓ Sample data in data/raw/ (2–3 files, 10+ rows each)

**Estimated Time**: 1–2 hours

---

## Issue #2: Implement ETL Ingest Module

**Title**: Build CSV/TSV reader with separator detection

**Description**:
Implement [src/etl/ingest.py](../src/etl/ingest.py):
- Auto-detect separator (comma, tab, semicolon)
- Normalize column names (lowercase, strip)
- Add audit columns: ingested_at, source_file, row_hash
- Support UTF-8 encoding

**Acceptance Criteria**:
- ✓ `ingest_file()` reads CSV/TSV and adds audit columns
- ✓ `ingest_all()` loads samples.csv, runs.csv, qc_metrics.tsv
- ✓ Test separators (comma, tab)
- ✓ Audit columns present in output

**Estimated Time**: 1 hour

---

## Issue #3: Implement Validation Rules

**Title**: Build comprehensive data quality checks

**Description**:
Implement [src/etl/validate.py](../src/etl/validate.py):
- Validate samples table (non-null, unique, valid platform)
- Validate runs table (FK, layout enum, numeric ranges)
- Validate QC metrics (Q30, GC%, duplication ranges)
- FK check: runs.sample_id in samples.sample_id
- Support strict/quarantine modes

**Validation Rules**:
- samples: sample_id unique+non-null, platform ∈ {ILLUMINA, NANOPORE, ...}
- runs: run_id unique+non-null, sample_id FK, layout ∈ {SINGLE, PAIRED}, read_length > 0
- qc_metrics: q30_rate ∈ [0,1], gc_percent ∈ [0,100], duplication ∈ [0,1]

**Acceptance Criteria**:
- ✓ 8+ validation tests pass
- ✓ Strict mode halts on errors
- ✓ Quarantine mode separates bad records
- ✓ All business rules enforced

**Estimated Time**: 1.5–2 hours

---

## Issue #4: Implement Transform Module

**Title**: Build type casting and normalization

**Description**:
Implement [src/etl/transform.py](../src/etl/transform.py):
- Normalize strings (trim, replace NA/null)
- Cast types (date, int, float)
- Uppercase enums (platform, library_layout)
- Deduplicate by primary keys (keep last)

**Transformations**:
- sample_id, run_id, project_id → trim, uppercase
- collection_date → parse as DATE
- read_length, total_reads → int64
- q30_rate, fastq_gb, gc_percent → float64
- library_layout → uppercase
- adapter_content_flag → boolean

**Acceptance Criteria**:
- ✓ 8+ transform tests pass
- ✓ All numeric columns have correct dtype
- ✓ Deduplication works (keeps last)
- ✓ Date parsing works (ISO 8601)

**Estimated Time**: 1.5 hours

---

## Issue #5: Implement Load Module (Parquet Writer)

**Title**: Write curated data to Parquet with partitioning

**Description**:
Implement [src/etl/load.py](../src/etl/load.py):
- Write dim_samples.parquet (dimension table)
- Write fact_runs.parquet (fact table with partitioning)
- Write fact_qc_metrics.parquet (fact table with partitioning)
- Use ZSTD compression
- Optional partitioning by project_id, platform

**Schema**:
- dim_samples: sample_id (PK), project_id, organism, collection_date, tissue, platform, audit columns
- fact_runs: run_id (PK), sample_id (FK), platform, library_layout, read_length, fastq_gb, audit columns
- fact_qc_metrics: run_id (FK), total_reads, q30_rate, gc_percent, duplication_rate, adapter_content_flag, audit columns

**Acceptance Criteria**:
- ✓ Parquet files created with correct schema
- ✓ Partitioning by project_id works (can be verified with pyarrow)
- ✓ File size < 1 MB for sample data
- ✓ ZSTD compression used

**Estimated Time**: 1 hour

---

## Issue #6: Build CLI with ETL Command

**Title**: Create Typer CLI for full pipeline

**Description**:
Implement [src/cli.py](../src/cli.py) with:
- `etl` command: ingest → validate → transform → load
- `query` command: run SQL against Parquet
- `benchmark` command: compare CSV vs Parquet
- `s3-push-cmd` / `s3-pull-cmd` for S3 (optional)
- Logging with --log-level option

**ETL Command Flags**:
```bash
python -m src.cli etl \
  --input data/raw \
  --output data/processed \
  --mode strict|quarantine \
  --log-level DEBUG|INFO|WARNING|ERROR
```

**Acceptance Criteria**:
- ✓ `etl` command runs full pipeline locally
- ✓ Logs show ingest/validate/transform/load steps
- ✓ data/processed/*.parquet created
- ✓ Strict mode aborts on errors
- ✓ Quarantine mode continues with valid data

**Estimated Time**: 1.5 hours

---

## Issue #7: Write SQL Queries

**Title**: Create 12 analytic queries for DuckDB

**Description**:
Implement [sql/queries.sql](../sql/queries.sql) with:

**Q1–Q3**: Basic analytics
- Q1: Samples/runs per project + storage
- Q2: Top 10 worst Q30 runs
- Q3: Multi-flag QC status

**Q4–Q6**: Intermediate analytics
- Q4: QC metrics by platform
- Q5: Total storage per project
- Q6: Window function ranking (worst Q30 per project)

**Q7–Q9**: Data quality
- Q7: Completeness (null %)
- Q8: Referential integrity (orphaned runs)
- Q9: Library layout distribution

**Q10–Q12**: Domain insights
- Q10: Platform-organism matrix
- Q11: Tissue-specific QC
- Q12: Temporal trends (collection date)

**Acceptance Criteria**:
- ✓ 12 queries in sql/queries.sql
- ✓ Each query runs without error
- ✓ Mix of: simple agg, joins, window functions, quality checks
- ✓ Example output in docs/example_output.md

**Estimated Time**: 2 hours

---

## Issue #8: Implement Benchmark Suite

**Title**: Compare CSV vs Parquet performance

**Description**:
Implement [src/benchmarks.py](../src/benchmarks.py):
- Benchmark file sizes (CSV vs Parquet)
- Benchmark query times (3 iterations, take median)
- Calculate speedup factor
- Generate markdown report

**Queries to Benchmark**:
1. Top 10 worst Q30
2. Sum FASTQ GB per project
3. Avg Q30 by platform

**Report Format**:
- File sizes table
- Query performance table (CSV, Parquet, Speedup)
- Conclusions (why Parquet is better)

**Acceptance Criteria**:
- ✓ Benchmark runs without error
- ✓ Report shows 10–30× speedup for Parquet
- ✓ Output: docs/benchmark_results.md
- ✓ Cost analysis included

**Estimated Time**: 1.5 hours

---

## Issue #9: Add Unit Tests

**Title**: Write tests for validate and transform modules

**Description**:
Implement tests in [tests/](../tests/):
- test_validate.py (8+ test cases)
- test_transform.py (8+ test cases)

**Test Cases (validate)**:
- test_valid_samples (pass)
- test_null_sample_id (fail)
- test_duplicate_sample_id (fail)
- test_invalid_platform (fail)
- test_invalid_read_length (fail)
- test_q30_out_of_range (fail)
- test_invalid_fk (fail)

**Test Cases (transform)**:
- test_trim_whitespace
- test_replace_na_strings
- test_uppercase
- test_numeric_casting
- test_date_parsing
- test_deduplication
- test_boolean_normalization

**Acceptance Criteria**:
- ✓ 16+ tests pass locally
- ✓ `pytest tests/ -v --cov=src` shows >80% coverage
- ✓ CI runs tests on Python 3.9, 3.10, 3.11

**Estimated Time**: 1.5–2 hours

---

## Issue #10: Write Documentation

**Title**: Create comprehensive docs for portfolio

**Description**:
Create documentation in [docs/](../docs/):

**Files to create**:
- [docs/data_dictionary.md](../docs/data_dictionary.md) — All columns, types, validation rules
- [docs/example_queries.md](../docs/example_queries.md) — 12 queries with explanations + example output
- [docs/SETUP.md](../docs/SETUP.md) — Development guide (testing, linting, debugging)
- [docs/benchmark_results.md](../docs/benchmark_results.md) — Performance analysis

**Data Dictionary Content**:
- Table schema (columns, types)
- Validation rules per table
- Relationships (FK, PK)
- Audit columns definition

**Example Queries Content**:
- Each query with explanation
- Expected output
- Use case / business question
- Performance notes

**Acceptance Criteria**:
- ✓ All 4 docs complete
- ✓ Recruiter can understand schema in 5 min
- ✓ Each query has clear business context
- ✓ Development guide enables contributions

**Estimated Time**: 2–3 hours

---

## Issue #11: Set Up GitHub Actions CI

**Title**: Automate testing, linting, type checking

**Description**:
Implement [.github/workflows/ci.yml](../.github/workflows/ci.yml):
- pytest on Python 3.9, 3.10, 3.11
- ruff linting
- black format check
- mypy type checking
- codecov upload

**Triggers**:
- On push to main/develop
- On pull requests

**Failure Conditions**:
- Test failure → block merge
- Lint failure → block merge
- Format mismatch → block merge
- Type error → warning (not blocking)

**Acceptance Criteria**:
- ✓ CI passes for main branch
- ✓ All checks run on PR
- ✓ Coverage report generated
- ✓ Badges in README

**Estimated Time**: 1 hour

---

## Issue #12: Add S3 Integration (Bonus)

**Title**: Implement boto3 push/pull to AWS S3

**Description**:
Implement [src/s3_handler.py](../src/s3_handler.py):
- `s3_push()` — Upload Parquet to S3
- `s3_pull()` — Download Parquet from S3
- CLI commands: `s3-push-cmd`, `s3-pull-cmd`
- Support .env for credentials
- Error handling for auth failures

**Usage**:
```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export S3_BUCKET=my-bucket

python -m src.cli s3-push-cmd --local-dir data/processed --prefix genomics/curated/
python -m src.cli s3-pull-cmd --prefix genomics/curated/ --local-dir data/download/
```

**Acceptance Criteria**:
- ✓ boto3 methods work
- ✓ Credentials from .env
- ✓ Error handling for missing bucket
- ✓ No secrets in repo (.env.example only)

**Estimated Time**: 1–1.5 hours

---

## Summary

| Issue | Title | Time | Total |
|-------|-------|------|-------|
| #1 | Initialize + CI | 1–2h | 1–2h |
| #2 | Ingest | 1h | 2–3h |
| #3 | Validate | 1.5–2h | 3.5–5h |
| #4 | Transform | 1.5h | 5–6.5h |
| #5 | Load (Parquet) | 1h | 6–7.5h |
| #6 | CLI | 1.5h | 7.5–9h |
| #7 | SQL Queries | 2h | 9.5–11h |
| #8 | Benchmark | 1.5h | 11–12.5h |
| #9 | Tests | 1.5–2h | 12.5–14.5h |
| #10 | Documentation | 2–3h | 14.5–17.5h |
| #11 | CI/CD | 1h | 15.5–18.5h |
| #12 | S3 (bonus) | 1–1.5h | 16.5–20h |

**Total Estimated Time**: 15–20 hours (depends on experience level)

---

## Getting Started

1. **Fork** the repo
2. **Work issues in order** (dependencies: #1 → #2–5 → #6 → #7–12)
3. **Test locally** before each PR
4. **Run CI** (`ruff check --fix && black . && pytest`)
5. **Document** with each change

**Recommended Workflow**:
- Tackle issues 1–6 in first week (MVP)
- Issues 7–9 in second week (analytics + tests)
- Issues 10–12 in third week (docs + polish)
