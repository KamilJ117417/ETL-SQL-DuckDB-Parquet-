# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-20

### Added

- **ETL Pipeline**: Complete ingest → validate → transform → load workflow
  - Ingest: CSV/TSV reader with auto-detection of separators and encoding
  - Validate: 8+ validation rules with strict/quarantine modes
  - Transform: Type casting, normalization, deduplication
  - Load: Parquet writer with partitioning support

- **SQL Analytics**: 12 example queries covering
  - Project/sample/run summaries
  - Quality control analysis (Q30, GC%, duplication)
  - Platform comparison
  - Temporal trends
  - Data quality metrics (completeness, referential integrity)

- **CLI**: Typer-based command interface
  - `etl` — Run full ETL pipeline
  - `query` — Execute SQL queries against Parquet
  - `benchmark` — Compare CSV vs Parquet performance
  - `s3-push-cmd` / `s3-pull-cmd` — AWS S3 integration (optional)

- **Benchmarking**: Performance comparison
  - CSV vs Parquet file sizes (~8× reduction)
  - Query performance (~13–26× faster on Parquet)
  - Storage cost analysis

- **Testing**: pytest suite with 16+ test cases
  - Validation tests (null checks, unique constraints, enums, ranges)
  - Transform tests (casting, normalization, dedup)
  - Integration tests (FK constraints)

- **Documentation**:
  - README with quick start and examples
  - Data dictionary with schema and validation rules
  - 12 example queries with detailed explanations
  - Development guide (SETUP.md)
  - Benchmark results with cost analysis

- **CI/CD**: GitHub Actions
  - pytest on Python 3.9–3.11
  - ruff linting
  - black formatting
  - mypy type checking

- **S3 Integration** (optional):
  - boto3-based push/pull
  - DuckDB httpfs support for reading Parquet from S3

### Technical Highlights

- **Languages**: Python 3.9+
- **Core Libraries**: pandas, PyArrow, DuckDB, Typer
- **Data Format**: Apache Parquet with ZSTD compression
- **Validation**: Pydantic-compatible enums and constraints
- **Partitioning**: Configurable by project_id, platform
- **Audit Trail**: ingested_at, source_file, row_hash columns

---

## Future Roadmap

### v0.2.0 (Planned)

- [ ] Streaming ingestion (Apache Kafka)
- [ ] Data profiling (Great Expectations)
- [ ] Incremental load (delta lake support)
- [ ] Web UI dashboard (Streamlit)
- [ ] Multi-file partitioning strategy
- [ ] Custom validation rule DSL

### v0.3.0 (Planned)

- [ ] BigQuery export
- [ ] Snowflake integration
- [ ] Time-series QC tracking
- [ ] Anomaly detection (isolation forest)
- [ ] SQL migration tooling

---

## Known Limitations

- Single-machine processing (not distributed)
- Small sample datasets (MVP examples < 1K rows)
- No real-time streaming
- S3 requires boto3 (not included by default)
- No authentication/authorization (adds own security layer)

---

## Contributors

- Kamil Jaworowski — Initial implementation

---

## Support

- 📖 [GitHub Wiki](https://github.com/yourusername/genomics-metadata-etl-duckdb/wiki)
- 💬 [Discussions](https://github.com/yourusername/genomics-metadata-etl-duckdb/discussions)
- 🐛 [Issue Tracker](https://github.com/yourusername/genomics-metadata-etl-duckdb/issues)
