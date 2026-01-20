# Example genomics metadata dataset (for genomics-metadata-etl-duckdb)

This folder contains small, realistic sample/run/QC metadata files for developing and testing an ETL pipeline.

## Folders
- `data/raw_clean/` — consistent dataset (should pass validation in strict mode)
- `data/raw_dirty/` — same dataset with *intentional* issues for validation/quarantine tests:
  1. duplicate `run_id` in `runs.csv`
  2. `runs.sample_id` referencing a non-existent sample (`SMP99999`)
  3. invalid QC values (`q30_rate < 0`, `gc_percent > 100`)
  4. missing required `run_id` in `qc_metrics.tsv`
  5. invalid `library_layout` value (`PAIRED-END`)
  6. malformed `collection_date` (`2024-13-40`)
  7. negative `fastq_gb`

## Files
- `samples.csv`
  - `sample_id` (PK), `project_id`, `organism`, `tissue`, `platform`, `collection_date`, `country`, `sex`, `age_years`
- `runs.csv`
  - `run_id` (PK), `sample_id` (FK), `project_id`, `library_layout`, `read_length`, `fastq_gb`, `library_strategy`, `insert_size`, `md5_1`, `md5_2`
- `qc_metrics.tsv`
  - `run_id` (FK), `project_id`, `total_reads`, `q30_rate`, `gc_percent`, `duplication_rate`, `adapter_content_flag`, `mean_quality`
- `variant_stats.csv` (optional)
  - `run_id`, `project_id`, `library_strategy`, `n_variants`, `ti_tv`, `heterozygosity_rate`, `variant_missing_rate`

## Suggested validation thresholds
- `q30_rate` in [0,1]
- `gc_percent` in [0,100]
- `duplication_rate` in [0,1]
- `read_length` > 0
- `fastq_gb` >= 0
- `library_layout` in {SINGLE, PAIRED}
