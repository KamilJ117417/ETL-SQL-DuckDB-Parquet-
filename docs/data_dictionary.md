# Data Dictionary

## Dimension Tables

### dim_samples.parquet

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| sample_id | string | Unique sample identifier | SAMPLE_001 |
| project_id | string | Project/study identifier | PRJNA001000 |
| organism | string | Organism name (scientific or common) | Homo sapiens |
| collection_date | date | When sample was collected | 2024-01-15 |
| tissue | string | Tissue/cell type | blood |
| platform | string | Sequencing platform | ILLUMINA |
| ingested_at | timestamp | When record was loaded into system | 2024-01-20T10:30:00 |
| source_file | string | Original source filename | samples.csv |
| row_hash | string | SHA256 hash of original record (for change detection) | abc123... |

## Fact Tables

### fact_runs.parquet

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| run_id | string | Unique sequencing run identifier | SRR123001 |
| sample_id | string | Foreign key to dim_samples | SAMPLE_001 |
| project_id | string | Project ID (for partitioning) | PRJNA001000 |
| platform | string | Sequencing platform (for partitioning) | ILLUMINA |
| library_layout | string | SINGLE or PAIRED-end | PAIRED |
| read_length | int | Length of reads in base pairs | 150 |
| fastq_gb | float | Size of FASTQ files in GB | 4.2 |
| md5_1 | string | MD5 checksum of first file (or only file if SINGLE) | abc123... |
| md5_2 | string | MD5 checksum of second file (PAIRED only) | def456... |
| ingested_at | timestamp | When record was loaded | 2024-01-20T10:30:00 |
| source_file | string | Original source filename | runs.csv |
| row_hash | string | SHA256 hash of original record | abc123... |

### fact_qc_metrics.parquet

| Column | Type | Description | Range/Values | Example |
|--------|------|-------------|---------------|---------|
| run_id | string | Foreign key to fact_runs | - | SRR123001 |
| project_id | string | Project ID (for partitioning) | - | PRJNA001000 |
| total_reads | int | Total number of reads sequenced | ≥ 0 | 125000000 |
| q30_rate | float | Fraction of bases with Phred quality ≥ 30 | [0, 1] | 0.92 |
| gc_percent | float | Percentage of GC bases in reads | [0, 100] | 48 |
| duplication_rate | float | Fraction of duplicate reads | [0, 1] | 0.15 |
| adapter_content_flag | bool | Whether adapter sequences detected | true/false | false |
| ingested_at | timestamp | When record was loaded | - | 2024-01-20T10:30:00 |
| source_file | string | Original source filename | - | qc_metrics.tsv |
| row_hash | string | SHA256 hash of original record | - | abc123... |

## Validation Rules

### Samples Table

- `sample_id` must be non-empty and unique
- `project_id` must be non-empty
- `platform` must be one of: ILLUMINA, NANOPORE, PACBIO, ION_TORRENT
- `collection_date` must be a valid date and not in the future
- `organism` and `tissue` must be non-empty

### Runs Table

- `run_id` must be non-empty and unique
- `sample_id` must be non-empty and exist in samples table (FK constraint)
- `library_layout` must be one of: SINGLE, PAIRED
- `read_length` must be > 0
- `fastq_gb` must be ≥ 0

### QC Metrics Table

- `run_id` must be non-empty
- `q30_rate` must be in [0, 1]
- `gc_percent` must be in [0, 100]
- `duplication_rate` must be in [0, 1]
- `adapter_content_flag` must be boolean

## Relationships

```
dim_samples (1)
    ↓ (sample_id)
fact_runs (N)
    ↓ (run_id)
fact_qc_metrics (N)
```

- Each sample can have multiple runs
- Each run can have multiple QC metric records
- Partitioning by `project_id` and `platform` enables fast filtering

## Data Types & Transformations

During ETL:

1. **Strings**: Trimmed, null-like values ("NA", "null", "") replaced with NULL
2. **Enums** (platform, library_layout): Converted to uppercase
3. **Dates**: Parsed as ISO 8601 (YYYY-MM-DD)
4. **Numerics**: Parsed as float/int; invalid values become NULL
5. **Booleans**: "true", "1", "yes" → true; others → false
6. **Deduplication**: Duplicate keys keep last occurrence (configurable)

## Audit Columns (in all tables)

- **ingested_at**: ISO 8601 timestamp of ETL load
- **source_file**: Original filename (samples.csv, runs.csv, qc_metrics.tsv)
- **row_hash**: SHA256 of raw record pre-transformation (enables change tracking)

## Example Queries

See [docs/example_queries.md](example_queries.md) and [sql/queries.sql](../sql/queries.sql) for 12+ analytical queries.
