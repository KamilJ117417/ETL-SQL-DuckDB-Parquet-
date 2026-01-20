.PHONY: install test lint format clean etl query benchmark gui help

help:
	@echo "Genomics Metadata ETL Pipeline"
	@echo ""
	@echo "Available commands:"
	@echo "  make install      - Install package and dependencies"
	@echo "  make test         - Run pytest"
	@echo "  make lint         - Run ruff and mypy"
	@echo "  make format       - Format code with black"
	@echo "  make clean        - Remove build artifacts and cache"
	@echo "  make etl          - Run ETL pipeline"
	@echo "  make query        - Run SQL queries"
	@echo "  make benchmark    - Run benchmark"
	@echo "  make gui          - Launch Streamlit GUI"

install:
	python -m venv .venv
	. .venv/bin/activate && pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

lint:
	ruff check src/ tests/
	mypy src/ --ignore-missing-imports || true

format:
	black src/ tests/
	ruff check --fix src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf .coverage htmlcov dist build *.egg-info

etl:
	python -m src.cli etl --input-dir data/raw --output-dir data/processed --mode strict --log-level INFO

query:
	python -m src.cli query --parquet data/processed --sql sql/queries.sql --output docs/query_results.md

benchmark:
	python -m src.cli benchmark --csv data/raw/runs.csv --parquet data/processed/fact_runs.parquet --output docs/benchmark_results.md

gui:
	@echo "🚀 Starting Streamlit GUI on port 8501..."
	@streamlit run app.py --server.port=8501 2>/dev/null || streamlit run app.py --server.port=8502

gui-advanced:
	@echo "🚀 Starting Advanced GUI on port 8501..."
	@streamlit run app_advanced.py --server.port=8501 2>/dev/null || streamlit run app_advanced.py --server.port=8502

kill-streamlit:
	@echo "🛑 Killing Streamlit processes..."
	@pkill -f streamlit || echo "No Streamlit processes found"
	@sleep 2
	@echo "✅ Done"
