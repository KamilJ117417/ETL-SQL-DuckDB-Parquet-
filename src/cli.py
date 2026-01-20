"""CLI entry point using Typer."""

import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from src.etl.ingest import ingest_all
from src.etl.validate import validate_all
from src.etl.transform import transform_all
from src.etl.load import load_to_processed
from src.etl.settings import ETLMode, LogLevel
from src.benchmarks import run_benchmark
from src.s3_handler import s3_push, s3_pull

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = typer.Typer(help="Genomics Metadata ETL Pipeline")


@app.command()
def etl(
    input_dir: Path = typer.Option("data/raw", help="Input directory with CSV/TSV files"),
    output_dir: Path = typer.Option("data/processed", help="Output directory for Parquet files"),
    mode: str = typer.Option("strict", help="ETL mode: strict or quarantine"),
    log_level: str = typer.Option("INFO", help="Log level: DEBUG, INFO, WARNING, ERROR"),
    partition_cols: Optional[str] = typer.Option(None, help="Comma-separated partition columns"),
) -> None:
    """
    Run full ETL pipeline: ingest → validate → transform → load.
    """
    # Set log level
    logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.info(f"Starting ETL pipeline with mode={mode}, log_level={log_level}")
    
    etl_mode = ETLMode(mode)
    
    try:
        # 1. Ingest
        logger.info("=== INGEST ===")
        input_dir = Path(input_dir)
        dfs = ingest_all(input_dir)
        
        if not dfs or "samples" not in dfs or "runs" not in dfs or "qc_metrics" not in dfs:
            logger.error("Failed to ingest required files")
            sys.exit(1)
        
        samples_df = dfs["samples"]
        runs_df = dfs["runs"]
        qc_df = dfs["qc_metrics"]
        
        # 2. Validate
        logger.info("=== VALIDATE ===")
        is_valid, errors = validate_all(samples_df, runs_df, qc_df, mode=etl_mode)
        
        if not is_valid:
            logger.warning(f"Found {len(errors)} validation errors:")
            for err in errors[:10]:  # Show first 10
                logger.warning(f"  {err}")
            
            if etl_mode == ETLMode.STRICT:
                logger.error("STRICT mode: aborting pipeline")
                sys.exit(1)
            else:
                logger.warning(f"QUARANTINE mode: continuing with valid records")
                # TODO: Save bad records to quarantine
        
        # 3. Transform
        logger.info("=== TRANSFORM ===")
        transformed = transform_all(samples_df, runs_df, qc_df)
        samples_df = transformed["samples"]
        runs_df = transformed["runs"]
        qc_df = transformed["qc_metrics"]
        
        logger.info(f"Samples: {len(samples_df)} records")
        logger.info(f"Runs: {len(runs_df)} records")
        logger.info(f"QC Metrics: {len(qc_df)} records")
        
        # 4. Load
        logger.info("=== LOAD ===")
        output_dir = Path(output_dir)
        parse_partition_cols = partition_cols.split(",") if partition_cols else None
        load_to_processed(samples_df, runs_df, qc_df, output_dir, partition_cols=parse_partition_cols)
        
        logger.info("✓ ETL pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}", exc_info=True)
        sys.exit(1)


@app.command()
def query(
    parquet_dir: Path = typer.Option("data/processed", help="Parquet directory"),
    sql_file: Optional[Path] = typer.Option(None, help="SQL file to run"),
    sql: Optional[str] = typer.Option(None, help="SQL query string"),
    output_file: Optional[Path] = typer.Option(None, help="Output file for results"),
) -> None:
    """
    Run SQL queries against Parquet files using DuckDB.
    """
    logger.info("Running SQL queries")
    
    # Validate that at least one input is provided
    if not sql_file and not sql:
        logger.error("Provide either --sql-file or --sql")
        sys.exit(1)
    
    try:
        import duckdb
        
        # Connect to DuckDB
        conn = duckdb.connect(":memory:")
        
        # Create views for each Parquet table
        parquet_dir = Path(parquet_dir)
        tables = ["dim_samples", "fact_runs", "fact_qc_metrics"]
        
        for table_name in tables:
            parquet_path = parquet_dir / f"{table_name}.parquet"
            if parquet_path.exists():
                conn.execute(f"CREATE VIEW {table_name.split('_', 1)[1] if '_' in table_name else table_name} AS SELECT * FROM read_parquet('{parquet_path}')")
                logger.info(f"Created view: {table_name}")
        
        # Run queries
        queries_to_run = []
        
        if sql:
            # Single SQL query from command line
            queries_to_run = [sql]
        elif sql_file:
            # Multiple queries from file
            sql_file = Path(sql_file)
            if not sql_file.exists():
                logger.error(f"SQL file not found: {sql_file}")
                sys.exit(1)
            
            with open(sql_file) as f:
                queries_to_run = f.read().split(";")
        
        results = []
        for i, query_str in enumerate(queries_to_run):
            query_str = query_str.strip()
            if query_str:
                logger.info(f"Executing query {i+1}...")
                result = conn.execute(query_str).fetchall()
                results.append((query_str, result))
        
        if output_file:
            with open(output_file, "w") as f:
                for query_str, result in results:
                    f.write(f"## Query\n{query_str}\n\n")
                    f.write(f"## Result\n{result}\n\n")
            logger.info(f"Results saved to {output_file}")
        else:
            for query_str, result in results:
                    print(f"\n{query_str}\n{result}")
        
        conn.close()
        
    except ImportError:
        logger.error("DuckDB not installed. Install with: pip install duckdb")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        sys.exit(1)


@app.command()
def benchmark(
    csv_file: Path = typer.Option("data/raw/runs.csv", help="CSV file to benchmark"),
    parquet_file: Path = typer.Option("data/processed/fact_runs.parquet", help="Parquet file to benchmark"),
    output_file: Optional[Path] = typer.Option(None, help="Output file for benchmark results"),
) -> None:
    """
    Run benchmark: CSV vs Parquet performance comparison.
    """
    logger.info("Running benchmarks")
    
    try:
        results = run_benchmark(csv_file, parquet_file)
        
        if output_file:
            with open(output_file, "w") as f:
                f.write("# Benchmark Results\n\n")
                f.write(results)
            logger.info(f"Benchmark results saved to {output_file}")
        else:
            print(results)
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        sys.exit(1)


@app.command()
def s3_push_cmd(
    local_dir: Path = typer.Option("data/processed", help="Local directory to push"),
    prefix: str = typer.Option("genomics/curated/", help="S3 prefix"),
) -> None:
    """Push files to S3."""
    logger.info(f"Pushing {local_dir} to S3://{prefix}")
    try:
        s3_push(local_dir, prefix)
        logger.info("✓ Push completed")
    except Exception as e:
        logger.error(f"S3 push failed: {e}", exc_info=True)
        sys.exit(1)


@app.command()
def s3_pull_cmd(
    prefix: str = typer.Option("genomics/curated/", help="S3 prefix"),
    local_dir: Path = typer.Option("data/s3_download/", help="Local directory"),
) -> None:
    """Pull files from S3."""
    logger.info(f"Pulling S3://{prefix} to {local_dir}")
    try:
        s3_pull(prefix, local_dir)
        logger.info("✓ Pull completed")
    except Exception as e:
        logger.error(f"S3 pull failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    app()
