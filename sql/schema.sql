-- DuckDB views over Parquet files
-- These create in-memory views that read directly from Parquet

CREATE OR REPLACE VIEW samples AS
SELECT * FROM read_parquet('data/processed/dim_samples.parquet');

CREATE OR REPLACE VIEW runs AS
SELECT * FROM read_parquet('data/processed/fact_runs.parquet');

CREATE OR REPLACE VIEW qc_metrics AS
SELECT * FROM read_parquet('data/processed/fact_qc_metrics.parquet');
