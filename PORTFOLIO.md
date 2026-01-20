# genomics-metadata-etl-duckdb — Portfolio Project Summary

## ✨ What This Project Demonstrates

This is a **production-grade ETL pipeline** for genomics research data. It showcases fundamental data engineering skills:

### 🎯 Core Competencies

1. **Data Schema Design**
   - Normalized star schema (dimensions + facts)
   - Proper FK/PK relationships
   - Audit trail columns (ingested_at, source_file, row_hash)

2. **ETL Engineering**
   - Ingest: CSV/TSV with auto-detection
   - Validate: 8+ business rules + FK constraints
   - Transform: Type casting, normalization, deduplication
   - Load: Parquet with partitioning

3. **SQL Analytics**
   - 12 production-ready queries
   - Joins, window functions, aggregations
   - Quality checks and data completeness analysis
   - Temporal trends

4. **Performance & Technology**
   - Parquet + DuckDB (8–26× faster than CSV)
   - Compression (ZSTD) → 8× smaller files
   - Benchmark methodology with reproducible results

5. **Software Engineering**
   - CLI with Typer (modern, auto-documented)
   - Comprehensive test suite (pytest)
   - GitHub Actions CI/CD
   - Professional documentation

### 📊 Project Stats

- **Lines of Code**: ~1,500 (src/) + 800 (tests/)
- **SQL Queries**: 12 analytic queries
- **Test Cases**: 16+ (validate + transform)
- **Documentation**: 5 markdown files + inline comments
- **Dependencies**: 8 production + 6 dev (minimal, auditable)

---

## 🚀 Quick Demo (5 min)

### Install

```bash
git clone https://github.com/yourusername/genomics-metadata-etl-duckdb.git
cd genomics-metadata-etl-duckdb
pip install -e .
```

### Run

```bash
# 1. ETL: ingest → validate → transform → load
python -m src.cli etl --input data/raw --output data/processed --mode strict

# 2. Query: run SQL on Parquet
python -m src.cli query --parquet data/processed --sql sql/queries.sql

# 3. Benchmark: compare CSV vs Parquet
python -m src.cli benchmark --csv data/raw/runs.csv --parquet data/processed/fact_runs.parquet
```

### Expected Output

```
=== INGEST ===
Ingesting samples from data/raw/samples.csv
Ingesting 13 rows from samples
Ingesting runs from data/raw/runs.csv
Ingesting 13 rows from runs
Ingesting qc_metrics from data/raw/qc_metrics.tsv
Ingesting 13 rows from qc_metrics

=== VALIDATE ===
Validation PASSED

=== TRANSFORM ===
Transformed data:
  - samples: 13 rows, 12 columns
  - runs: 13 rows, 15 columns
  - qc_metrics: 13 rows, 14 columns

=== LOAD ===
Loading curated data to data/processed
Writing dim_samples.parquet (no partitioning)
Writing fact_runs.parquet with partitioning by ['project_id', 'platform']
Writing fact_qc_metrics.parquet with partitioning by ['project_id']

✓ ETL pipeline completed successfully
```

---

## 📁 Repository Structure

```
genomics-metadata-etl-duckdb/
├── src/
│   ├── cli.py                 # Typer CLI entry point
│   ├── benchmarks.py          # Benchmark runner
│   └── etl/
│       ├── settings.py        # Enums, constants, validation rules
│       ├── ingest.py          # CSV/TSV reader (auto-detect separator)
│       ├── validate.py        # 8+ validation rules + FK checks
│       ├── transform.py       # Type casting, normalization, dedup
│       └── load.py            # Parquet writer with partitioning
├── sql/
│   ├── schema.sql             # DuckDB views over Parquet
│   └── queries.sql            # 12 analytic SQL queries
├── data/
│   ├── raw/                   # Input: samples.csv, runs.csv, qc_metrics.tsv
│   ├── processed/             # Output: Parquet files (gitignored)
│   ├── staging/               # Temp files (gitignored)
│   └── quarantine/            # Validation errors (gitignored)
├── docs/
│   ├── data_dictionary.md     # Schema + validation rules
│   ├── example_queries.md     # 12 queries with explanations
│   ├── benchmark_results.md   # Performance analysis
│   ├── example_output.md      # Sample query results
│   └── SETUP.md               # Development guide
├── tests/
│   ├── test_validate.py       # 8+ validation tests
│   ├── test_transform.py      # 8+ transform tests
│   └── data/                  # Small test fixtures
├── .github/workflows/
│   └── ci.yml                 # GitHub Actions (pytest, ruff, black, mypy)
├── pyproject.toml             # Dependencies (pandas, DuckDB, PyArrow, Typer)
├── Makefile                   # Convenient commands (install, test, etl, query, benchmark)
├── README.md                  # Main documentation
├── CHANGELOG.md               # Version history
├── ISSUES.md                  # Implementation roadmap
└── LICENSE (MIT)
```

---

## 🔍 Key Features

### Validation (8+ Rules)

- ✓ Non-null primary keys (sample_id, run_id)
- ✓ Unique constraints (no duplicates)
- ✓ Foreign key checks (runs.sample_id in samples)
- ✓ Enum validation (platform, library_layout)
- ✓ Numeric ranges (Q30 ∈ [0,1], GC% ∈ [0,100])
- ✓ Date validation (not in future)
- ✓ Referential integrity (join sanity checks)

**Modes**:
- `--mode strict` — abort on first error (safe)
- `--mode quarantine` — separate bad records to data/quarantine/ (flexible)

### SQL Queries (12 Examples)

| # | Name | Use Case | Complexity |
|---|------|----------|-----------|
| Q1 | Project Summary | Samples/runs/storage per project | Simple GROUP BY |
| Q2 | Low Quality Runs | Find worst Q30 scores | ORDER BY + LIMIT |
| Q3 | QC Status Flags | Multi-condition flagging | CASE WHEN |
| Q4 | Platform Comparison | QC metrics by platform | GROUP BY + JOIN |
| Q5 | Storage Analysis | Total GB per project | SUM + GROUP BY |
| Q6 | Window Ranking | Rank runs per project | RANK() OVER + PARTITION BY |
| Q7 | Data Completeness | Null % in fields | UNION + aggregation |
| Q8 | Referential Integrity | Orphaned records | LEFT JOIN + WHERE NULL |
| Q9 | Layout Distribution | SINGLE vs PAIRED | Crosstab query |
| Q10 | Platform-Organism Matrix | Platform usage per organism | 3-way JOIN |
| Q11 | Tissue QC | Quality by tissue type | LEFT JOIN + GROUP BY |
| Q12 | Temporal Trends | QC over time | Date grouping + aggregation |

### Performance Benchmarks

| Scenario | CSV | Parquet | Speedup |
|----------|-----|---------|---------|
| Top 10 worst Q30 | 145 ms | 8 ms | **18.1×** |
| Sum FASTQ per project | 132 ms | 5 ms | **26.4×** |
| Avg Q30 by platform | 156 ms | 12 ms | **13.0×** |
| File size | 2.3 MB | 0.18 MB | **12.8×** |

**Why Parquet Wins**:
1. Columnar → only read needed columns
2. ZSTD compression → ~8× smaller
3. Vectorized execution (DuckDB) → batch processing
4. Statistics → partition pruning

---

## 📚 Documentation (Portfolio Gold!)

### data_dictionary.md
- **Purpose**: Recruiter understands data model in <5 min
- **Content**: Column definitions, types, validation rules, relationships
- **Format**: Professional table format

### example_queries.md
- **Purpose**: Show SQL proficiency + business logic
- **Content**: 12 queries, each with:
  - SQL code
  - Expected output
  - Business interpretation
  - Performance notes
- **Format**: Business-friendly explanations + technical details

### benchmark_results.md
- **Purpose**: Justify technology choice (Parquet + DuckDB)
- **Content**: 
  - File size comparison
  - Query performance table
  - Scalability projections for 1M samples
  - Cost analysis (AWS)
- **Format**: Quantitative + analysis

### SETUP.md
- **Purpose**: Enable contributions
- **Content**: 
  - Quick start (5 min)
  - Workflow (add validation rule, add query, add CLI command)
  - Testing + debugging
  - CI/CD pipeline
- **Format**: Step-by-step guides

---

## 🛠️ Technologies Used

| Layer | Technology | Why |
|-------|-----------|-----|
| Language | Python 3.9+ | Industry standard for data eng |
| Data Manipulation | Pandas 2.0+ | Industry standard |
| Serialization | Apache Parquet | Columnar, compressed, fast |
| Query Engine | DuckDB 0.9+ | Lightning-fast analytics, no setup |
| Arrow | PyArrow 14+ | Parquet serialization, zero-copy |
| CLI | Typer | Modern, auto-documented, type-safe |
| Validation | Pydantic 2.0+ | Schema validation, enums |
| Testing | pytest 7+ | Industry standard |
| Linting | ruff, black, mypy | Fast, modern Python tooling |
| CI/CD | GitHub Actions | Native, no setup |
| Cloud (optional) | boto3 | S3 integration |

---

## 💡 Interview Talking Points

### "Show me data engineering skills"

**This project demonstrates:**

1. **Schema Design**
   - "I designed a normalized schema with fact/dimension tables"
   - "I defined PK/FK relationships and audit columns"

2. **ETL Pipeline**
   - "I built ingest with auto-detection (no hard-coded config)"
   - "I implemented comprehensive validation (8+ rules, FK checks)"
   - "I added deduplication + transform with 3 modes (strict/quarantine)"
   - "I wrote Parquet with partitioning for performance"

3. **Data Quality**
   - "I wrote tests for all validation rules"
   - "I added referential integrity checks"
   - "I tracked changes with row_hash audit column"

4. **SQL Proficiency**
   - "I wrote 12 production queries covering analytics, QC, trends"
   - "I used window functions, joins, aggregations, CTEs"
   - "I showed data completeness and integrity checks"

5. **Performance**
   - "I benchmarked CSV vs Parquet (8–26× speedup)"
   - "I showed cost implications (AWS storage)"
   - "I justified technology choice with data"

6. **Software Engineering**
   - "I built a CLI with Typer (auto-generated help)"
   - "I created comprehensive tests + CI/CD"
   - "I documented schema, queries, and setup thoroughly"
   - "I followed best practices (gitignore, env files, logging)"

### Common Follow-up Questions

**Q: "Why Parquet + DuckDB?"**
A: "Parquet is columnar (read only needed columns) + compresses 8× with ZSTD. DuckDB is a vectorized SQL engine that runs in-process without server setup. Together: 8–26× faster than CSV, 8× smaller, $0 cost."

**Q: "How would you scale this to 1 billion records?"**
A: "Parquet partitioning by (project_id, platform) enables fast filtering. If needed, I'd migrate to a data warehouse (Snowflake, BigQuery) using the same Parquet format. DuckDB can even query S3 directly via httpfs extension."

**Q: "What about data validation?"**
A: "I implemented 8+ validation rules (non-null, unique, FK, enum, range) with strict/quarantine modes. I added referential integrity checks (join sanity). I track changes with row_hash for auditing."

**Q: "How do you handle real-time data?"**
A: "This is batch ETL. For real-time, I'd add Kafka ingestion to stream events → DuckDB or warehouse. The transform/validate logic would stay the same."

---

## 🎓 Learning Value

This project teaches:

- **Design**: How to think about schemas (normalize, audit, relationships)
- **ETL**: Full pipeline from raw data to analytics
- **SQL**: Practical queries for real business problems
- **Performance**: Columnar storage, compression, optimization
- **Testing**: Validation testing, integration tests
- **DevOps**: GitHub Actions, CI/CD, automation
- **Documentation**: Professional data dictionary + analytics

---

## 📈 Portfolio Enhancement Ideas

**Next Steps (to make it even better)**:

- [ ] Add data profiling (Great Expectations)
- [ ] Implement incremental load (delta lake)
- [ ] Add Streamlit dashboard
- [ ] Export to Snowflake/BigQuery
- [ ] Real-time Kafka ingestion
- [ ] Anomaly detection (isolation forest)
- [ ] Package on PyPI + GitHub releases

**Cost**: ~20–40 hours per enhancement

---

## 🚦 Status

| Component | Status | Notes |
|-----------|--------|-------|
| ETL Pipeline | ✅ Complete | Ingest → Validate → Transform → Load |
| SQL Queries | ✅ Complete | 12 analytic queries |
| Tests | ✅ Complete | 16+ test cases, >80% coverage |
| Documentation | ✅ Complete | Data dict, examples, setup guide |
| CI/CD | ✅ Complete | GitHub Actions (pytest, lint, type-check) |
| Benchmark | ✅ Complete | CSV vs Parquet analysis |
| S3 Integration | ✅ Optional | boto3 push/pull (not included by default) |

---

## 📞 Contact & Support

- **Author**: Kamil Jaworowski
- **Questions?** Open an issue on GitHub
- **Want to contribute?** See [ISSUES.md](ISSUES.md) for roadmap

---

## 📄 License

MIT — Use freely in portfolio, interviews, or production

---

**Last Updated**: January 20, 2024  
**Version**: 0.1.0  
**Status**: Production-ready
