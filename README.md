# 🧬 genomics-metadata-etl-duckdb

**Production-grade ETL pipeline for genomics metadata with advanced GUI, data profiling, automated reporting, QC analysis, schema validation, audit logging, batch processing, and job scheduling.**


## Overview

This project demonstrates a production-grade ETL pipeline for genomics metadata. It showcases:

- **Data schema design** (normalized star schema: dimensions + facts)
- **ETL engineering** (validation, normalization, deduplication, audit logging)
- **SQL analytics** (joins, window functions, aggregations, quality checks)
- **Advanced profiling** (data quality scores, outlier detection, before/after comparison)
- **Genomics QC** (Q30, GC%, duplication, adapter content analysis)
- **Automated reporting** (HTML/Markdown with visualizations and recommendations)
- **Enterprise features** (history tracking, job scheduling, batch uploads, schema validation)
- **Performance** (Parquet + DuckDB benchmarks vs. CSV — 13-26× speedup)
- **Cloud-ready** (optional S3 integration)

## Architecture

```
RAW (CSV/TSV)
    ↓
INGEST (mapping, encoding detection)
    ↓
STAGING (schema, audit columns)
    ↓
VALIDATE (FK checks, business rules)
    ↓
TRANSFORM (types, normalization, dedup)
    ↓
LOAD → Parquet (partitioned)
    ↓
DuckDB SQL Analytics
```

## Data Model

### Input Files (data/raw/)

- **samples.csv** — Sample metadata (project, organism, tissue, platform)
- **runs.csv** — Sequencing runs (sample references, layout, file sizes, checksums)
- **qc_metrics.tsv** — Quality control metrics (Q30, GC%, duplication, adapters)

### Curated Parquet Tables (data/processed/)

- **dim_samples.parquet** — Dimension table for samples (PK: sample_id)
- **fact_runs.parquet** — Fact table for runs (PK: run_id, FK: sample_id)
- **fact_qc_metrics.parquet** — Fact table for QC (FK: run_id)

See [docs/data_dictionary.md](docs/data_dictionary.md) for full schema.

## Quickstart

### 🚀 Launch Advanced GUI (Recommended)

```bash
# Install dependencies
pip install -e ".[dev]"
pip install plotly schedule

# Run advanced GUI with 11 professional tabs
streamlit run app_advanced.py

# Or use make target
make gui-advanced
```

**Browser**: Open http://localhost:8501

**11 GUI Tabs:**
1. 🚀 **Pipeline** — Run ETL (INGEST → VALIDATE → TRANSFORM → LOAD)
2. 📊 **Data Profiling** — Quality scores, column stats, missing data analysis
3. 📈 **QC Metrics** — Q30, GC%, duplication, adapter content (genomics-specific)
4. 🔍 **SQL Queries** — Predefined + custom SQL queries with CSV download
5. ⚡ **Benchmark** — CSV vs Parquet performance comparison
6. 🔄 **Comparison** — Before/After data analysis
7. 📋 **Schema** — Parquet/CSV schema inspection and validation
8. 📁 **Upload** — Multi-file batch processing with validation
9. 📄 **Reports** — Generate and download HTML/Markdown reports
10. 📅 **Scheduling** — Create recurring pipeline jobs (cron-like)
11. 🕐 **History** — Audit logs, execution statistics, history export

---

### 1. Install

**Option A: Full Installation (Recommended)**

```bash
git clone https://github.com/yourusername/genomics-metadata-etl-duckdb.git
cd genomics-metadata-etl-duckdb

python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install pandas>=2.0.0 duckdb>=0.9.0 pyarrow>=14.0.0 pydantic>=2.0.0 typer>=0.9.0 python-dotenv>=1.0.0 boto3>=1.28.0

# Install dev tools + advanced edition dependencies (v2.0)
pip install pytest>=7.4.0 pytest-cov>=4.1.0 black>=23.0.0 ruff>=0.1.0 mypy>=1.5.0
pip install streamlit>=1.28.0 plotly>=5.17.0 schedule>=1.2.0 jinja2>=3.1.0 psutil>=5.9.0
```

**Option B: Quick Install**

```bash
cd genomics-metadata-etl-duckdb
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$(pwd)"
pip install -e ".[dev]"
pip install plotly schedule
bash test_imports.sh  # Verify imports work
```

### 2. Run ETL

**Option A: Using Streamlit GUI** ⭐ **Recommended**
```bash
streamlit run app_advanced.py
# Click "🚀 Pipeline" tab → "RUN ETL PIPELINE" button
```

**Option B: Using CLI**
```bash
python -m src.cli etl \
  --input-dir data/raw \
  --output-dir data/processed \
  --mode strict
```

**Option C: Direct Python**
```bash
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from src.etl.ingest import ingest_all
from src.etl.validate import validate_all
from src.etl.transform import transform_all
from src.etl.load import load_to_processed
from src.etl.settings import ETLMode

dfs = ingest_all(Path('data/raw'))
is_valid, errors = validate_all(dfs['samples'], dfs['runs'], dfs['qc_metrics'], mode=ETLMode.STRICT)
transformed = transform_all(dfs['samples'], dfs['runs'], dfs['qc_metrics'])
load_to_processed(transformed['samples'], transformed['runs'], transformed['qc_metrics'], Path('data/processed'))
print("✓ ETL completed!")
EOF
```

**Modes:**
- `strict` — stop on any validation error (recommended)
- `quarantine` — save bad records to data/quarantine/, continue

### 3. Analyze Data

**Via Streamlit GUI** ⭐ **Recommended**:
```bash
streamlit run app_advanced.py
# Click on any analysis tab: 📊 Profiling, 📈 QC Metrics, 🔄 Comparison, etc.
```

### 4. Run SQL Queries

**Via Streamlit GUI** ⭐ **Recommended**:
```bash
streamlit run app_advanced.py
# Click "🔍 SQL Queries" tab → select predefined or write custom SQL
```

**Via CLI**:
```bash
python -m src.cli query --sql "SELECT COUNT(*) as samples FROM samples"
```

**Direct Python**:
```bash
python3 << 'EOF'
import duckdb

conn = duckdb.connect(':memory:')
conn.execute("CREATE VIEW samples AS SELECT * FROM read_parquet('data/processed/dim_samples.parquet')")
conn.execute("CREATE VIEW runs AS SELECT * FROM read_parquet('data/processed/fact_runs.parquet')")
conn.execute("CREATE VIEW qc_metrics AS SELECT * FROM read_parquet('data/processed/fact_qc_metrics.parquet')")

# Example: Project summary
result = conn.execute("""
  SELECT
    s.project_id,
    COUNT(DISTINCT s.sample_id) AS n_samples,
    COUNT(DISTINCT r.run_id)    AS n_runs
  FROM samples s
  LEFT JOIN runs r USING(sample_id)
  GROUP BY 1
  ORDER BY n_runs DESC
""").fetchall()

print("Project Summary:")
for row in result:
    print(f"  {row}")
EOF
```

### 5. Benchmark & Generate Reports

**Via Streamlit GUI** ⭐ **Recommended**:
```bash
streamlit run app_advanced.py

# Performance Benchmark
# Click "⚡ Benchmark" tab → "RUN BENCHMARK"

# Generate Reports
# Click "📄 Reports" tab → Select HTML or Markdown → "GENERATE" → Download
```

**See full results** in [docs/benchmark_results.md](docs/benchmark_results.md) showing 8–26× speedup with Parquet.

### 6. Schedule Automatic Runs

**Via Streamlit GUI**:
```bash
streamlit run app_advanced.py
# Click "📅 Scheduling" tab → Set interval → "CREATE SCHEDULE"
```

### 7. View Audit History

**Via Streamlit GUI**:
```bash
streamlit run app_advanced.py
# Click "🕐 History" tab → View past runs & statistics
```

---

### 1️⃣ **Data Profiling & Quality Scoring**

```python
from src.profiling import profile_dataframe, data_quality_report, compare_dataframes

profile = profile_dataframe(df)           # Column stats, missing data
quality = data_quality_report(df)         # Quality score (0-100)
comparison = compare_dataframes(df_before, df_after, "Raw", "Processed")
```

### 2️⃣ **Automated Report Generation**

```python
from src.reporting import generate_html_report, generate_markdown_report

html_path = generate_html_report(pipeline_results, profile_results)
md_path = generate_markdown_report(pipeline_results, profile_results)
```

### 3️⃣ **Genomics QC Metrics**

```python
from src.qc_metrics import analyze_qc_metrics, get_failed_samples

analysis = analyze_qc_metrics(qc_df)    # Q30, GC%, duplication, adapters
failed = get_failed_samples(qc_df)      # Samples outside thresholds
```

### 4️⃣ **Schema Validation**

```python
from src.schema_inspector import inspect_parquet_schema, compare_schemas

schema_pq = inspect_parquet_schema(Path("data/processed/samples.parquet"))
schema_csv = inspect_csv_schema(Path("data/raw/samples.csv"))
comparison = compare_schemas(schema_csv, schema_pq)
```

### 5️⃣ **Pipeline History & Audit Log**

```python
from src.history import log_pipeline_run, get_pipeline_history

log_pipeline_run(status="success", samples=30, runs=48, duration=12.5)
history = get_pipeline_history(limit=50)
```

### 6️⃣ **Job Scheduling**

```python
from src.scheduler import create_etl_schedule, start_scheduler

create_etl_schedule(interval=24, unit="hours")
start_scheduler()  # Background thread
```

### 7️⃣ **Batch File Upload**

```python
from src.file_upload import batch_process_files

results = batch_process_files(file_list, process_func, Path("data/raw"))
```

## Example Queries

### Samples and runs per project

```sql
SELECT
  s.project_id,
  COUNT(DISTINCT s.sample_id) AS n_samples,
  COUNT(DISTINCT r.run_id)    AS n_runs
FROM samples s
LEFT JOIN runs r USING(sample_id)
GROUP BY 1
ORDER BY n_runs DESC;
```

### Top 10 runs with worst Q30 (low quality)

```sql
SELECT
  r.project_id,
  q.run_id,
  q.q30_rate,
  q.total_reads
FROM qc_metrics q
JOIN runs r USING(run_id)
ORDER BY q.q30_rate ASC
LIMIT 10;
```

### Quality control status flags

```sql
SELECT
  r.project_id,
  q.run_id,
  CASE
    WHEN q.q30_rate < 0.85 THEN 'LOW_Q30'
    WHEN q.duplication_rate > 0.6 THEN 'HIGH_DUP'
    WHEN q.adapter_content_flag THEN 'ADAPTERS'
    ELSE 'OK'
  END AS qc_status
FROM qc_metrics q
JOIN runs r USING(run_id);
```

More examples in [docs/example_queries.md](docs/example_queries.md).

---

## 📊 Benchmark Results

| Scenario | CSV Time (ms) | Parquet Time (ms) | Speedup | CSV Size (MB) | Parquet Size (MB) |
|----------|---------------|-------------------|---------|---------------|-------------------|
| Top 10 worst Q30 | 145 | 8 | 18.1× | 2.3 | 0.18 |
| Sum FASTQ per project | 132 | 5 | 26.4× | 2.3 | 0.18 |
| Avg Q30 per platform | 156 | 12 | 13.0× | 2.3 | 0.18 |

See full results in [docs/benchmark_results.md](docs/benchmark_results.md).

**Why this matters:**
- Parquet is columnar → reads only needed columns
- Compression + ZSTD encoding → ~8x smaller
- DuckDB vectorized execution + partition pruning → orders of magnitude faster

## Development

### Run Tests

```bash
pytest tests/ -v --cov=src
```

### Lint & Format

```bash
ruff check src/ tests/
black src/ tests/
mypy src/
```

### CI

Push to `main` triggers GitHub Actions:
- pytest
- ruff lint
- black format check
- type checking with mypy

## S3 Integration (Optional)

To push/pull from AWS S3:

```bash
# 1. Set environment variables (.env)
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
export S3_BUCKET=my-genomics-bucket

# 2. Push processed data to S3
python -m src.cli s3 push \
  --local data/processed \
  --prefix genomics/curated/

# 3. Pull from S3
python -m src.cli s3 pull \
  --prefix genomics/curated/ \
  --local data/s3_download/
```

See [.env.example](.env.example) for required variables.

**Security note:** Use IAM user with minimal permissions (S3 bucket + prefix only).

## Project Structure

```
genomics-metadata-etl-duckdb/
├── src/
│   ├── __init__.py
│   ├── cli.py                 # CLI interface (typer)
│   ├── benchmarks.py          # Performance benchmarking
│   ├── s3_handler.py          # AWS S3 integration
│   ├── profiling.py           # Data quality profiling
│   ├── reporting.py           # Report generation (HTML/MD)
│   ├── history.py             # Pipeline audit log (SQLite)
│   ├── scheduler.py           # Job scheduling
│   ├── schema_inspector.py    # Schema validation
│   ├── file_upload.py         # Batch file processing
│   ├── qc_metrics.py          # Genomics QC analysis
│   └── etl/
│       ├── __init__.py
│       ├── ingest.py          # CSV/TSV reader
│       ├── validate.py        # Validation rules
│       ├── transform.py       # Normalization & dedup
│       ├── load.py            # Parquet writer (partitioned)
│       └── settings.py        # Config & enums
├── sql/
│   ├── schema.sql             # DuckDB views
│   └── queries.sql            # Example queries
├── data/
│   ├── raw/                   # Input CSV/TSV
│   ├── processed/             # Output Parquet (gitignored)
│   ├── staging/               # Temp (gitignored)
│   └── quarantine/            # Failed records (gitignored)
├── docs/
│   ├── data_dictionary.md     # Schema definitions
│   ├── example_queries.md     # Query examples
│   ├── benchmark_results.md   # Performance analysis
│   ├── ADVANCED_FEATURES.md   # Features guide
│   ├── DEPLOYMENT_GUIDE.md    # Production deployment
│   └── STREAMLIT_README.md    # GUI documentation
├── tests/
│   ├── test_validate.py
│   ├── test_transform.py
│   └── data/                  # Test fixtures
├── .github/workflows/
│   └── ci.yml                 # GitHub Actions
├── .gitignore
├── .env.example
├── app.py                     # Basic Streamlit GUI
├── app_advanced.py            # Advanced Streamlit GUI (11 tabs)
├── pyproject.toml
├── setup.py
├── Makefile
├── README.md
└── LICENSE
```

---

## 🛠️ Development
│       └── settings.py        # Config + enums
├── sql/
│   ├── schema.sql             # DuckDB views over Parquet
│   ├── queries.sql            # 8–12 analytic queries
│   └── views.sql              # (optional) materialized views
├── data/
│   ├── raw/                   # Input CSV/TSV (small examples)
│   │   ├── samples.csv
│   │   ├── runs.csv
│   │   └── qc_metrics.tsv
│   ├── processed/             # Output Parquet (gitignored)
│   ├── staging/               # Temp staging (gitignored)
│   └── quarantine/            # Failed validation (gitignored)
├── docs/
│   ├── data_dictionary.md     # Column definitions
│   ├── example_queries.md     # Full query examples
│   └── benchmark_results.md   # Benchmark tables & analysis
├── tests/
│   ├── test_validate.py
│   ├── test_transform.py
│   └── data/                  # Small test fixtures
├── .github/workflows/
│   └── ci.yml                 # GitHub Actions
├── .gitignore
├── .env.example
├── pyproject.toml
├── Makefile                   # (optional) convenient targets
└── README.md
```

## 🛠️ Development

### Run Tests

```bash
pytest tests/ -v --cov=src
```

### Lint & Format

```bash
ruff check src/ tests/
black src/ tests/
mypy src/
```

### Make Targets

```bash
make etl               # Run ETL pipeline
make query             # Run SQL queries
make benchmark         # Run benchmarks
make gui               # Launch basic Streamlit GUI
make gui-advanced      # Launch advanced Streamlit GUI (v2.0)
make test              # Run pytest
make lint              # Run linter
```

### CI/CD

Push to `main` triggers GitHub Actions:
- pytest with coverage
- ruff lint
- black format check
- mypy type checking

---

## 🔐 Validation Rules

The pipeline enforces:

- **sample_id, run_id** must be non-empty and unique
- **runs.sample_id** must exist in samples (FK check)
- **q30_rate** ∈ [0, 1]
- **gc_percent** ∈ [0, 100]
- **library_layout** ∈ {SINGLE, PAIRED}
- **collection_date** not in future
- **read_length > 0**, **fastq_gb ≥ 0**

See [src/etl/validate.py](src/etl/validate.py) for implementation.

---

## 📝 Audit Columns

All curated tables include:

- **ingested_at** — Timestamp of ingestion
- **source_file** — Original file name
- **row_hash** — SHA256 of raw record (detect changes)

---

## 🔑 Key Technologies

**Core:**
- **Pandas, PyArrow, DuckDB** — High-performance data processing
- **Typer, Pydantic** — CLI & validation

**Advanced Edition (v2.0):**
- **Streamlit, Plotly** — Interactive web UI with charts
- **Schedule, SQLite, Jinja2, psutil** — Job scheduling, audit logs, templates, monitoring

**DevOps:**
- **pytest, GitHub Actions** — Testing & CI/CD

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) | v2.0 features, 9 new modules, 11 GUI tabs |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Docker, Kubernetes, AWS deployment |
| [STREAMLIT_README.md](STREAMLIT_README.md) | GUI usage, configuration, troubleshooting |
| [docs/data_dictionary.md](docs/data_dictionary.md) | Schema definitions |
| [docs/example_queries.md](docs/example_queries.md) | SQL query examples |
| [docs/benchmark_results.md](docs/benchmark_results.md) | Performance analysis |

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/my-feature`
3. Run tests: `pytest tests/ -v`
4. Format code: `black src/ tests/` and `ruff check src/ tests/`
5. Push and open a PR

---

## 📄 License

MIT

---

## 👤 Author

**Kamil Jaworowski**

---

## 🚀 Quick Navigation

- **Want to run?** → [Quickstart](#quickstart)
- **Want to understand features?** → [Advanced Features (v2.0)](#-advanced-features-v20)
- **Want to deploy?** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Want to extend?** → [Contributing](#-contributing)
- **Want to see SQL examples?** → [Example Queries](#example-queries)
- **Want benchmarks?** → [Benchmark Results](#-benchmark-results)

---
