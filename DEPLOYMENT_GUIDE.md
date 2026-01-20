# 🧬 Genomics ETL Pipeline — Configuration & Deployment Guide

## 📋 Spis Treści

1. [Quick Start](#quick-start)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage Examples](#usage-examples)
6. [Troubleshooting](#troubleshooting)
7. [Production Deployment](#production-deployment)

---

## 🚀 Quick Start

### Instalacja (< 5 minut)

```bash
# 1. Clone repository
git clone https://github.com/KamilJ117417/ETL-SQL-DuckDB-Parquet-.git
cd ETL-SQL-DuckDB-Parquet-

# 2. Run setup script
bash setup_advanced.sh

# 3. Run application
streamlit run app_advanced.py
```

Aplikacja otworzy się na: **http://localhost:8501**

---

## 💻 System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| Python | 3.9+ | 3.10+ |
| RAM | 2 GB | 4+ GB |
| Disk | 1 GB | 10+ GB |
| OS | Linux/Mac/Windows | Linux |

---

## 📦 Installation

### Option 1: Automated (Recommended)

```bash
bash setup_advanced.sh
```

### Option 2: Manual

```bash
# Install package in development mode
pip install -e ".[dev]"

# Install additional dependencies
pip install streamlit>=1.28.0
pip install plotly>=5.17.0
pip install schedule>=1.2.0
pip install jinja2>=3.1.0
pip install psutil>=5.9.0
```

### Option 3: Docker

```bash
docker build -t genomics-etl:latest .
docker run -p 8501:8501 -v $(pwd)/data:/app/data genomics-etl:latest
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file:

```bash
# AWS S3 (optional)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=genomics-data

# Logging
LOG_LEVEL=INFO

# ETL
ETL_MODE=strict
PARTITION_COLUMNS=project_id,platform
COMPRESS_METHOD=zstd

# Scheduling (optional)
SCHEDULE_ENABLED=true
SCHEDULE_INTERVAL=24
SCHEDULE_UNIT=hours
```

### Streamlit Config

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[client]
showErrorDetails = true
toolbarMode = "developer"

[logger]
level = "info"

[server]
port = 8501
headless = true
runOnSave = true
```

---

## 📚 Usage Examples

### Example 1: Basic Pipeline Run

```bash
# Via CLI
python run_etl_new_data.py

# Via Make
make etl

# Via Streamlit GUI
streamlit run app_advanced.py
# Then click "🚀 Pipeline" → "RUN ETL PIPELINE"
```

### Example 2: Data Profiling

```python
from src.profiling import profile_dataframe, data_quality_report
import pandas as pd

df = pd.read_csv("data/raw/samples.csv")
profile = profile_dataframe(df)
quality = data_quality_report(df)

print(f"Quality Score: {quality['quality_score']:.1f}%")
print(f"Missing Cells: {quality['missing_cells']}")
```

### Example 3: Generate Reports

```python
from src.reporting import generate_html_report, generate_markdown_report
from pathlib import Path

pipeline_results = {"samples": 30, "runs": 48, "qc_metrics": 48}
profile_results = {"quality_score": 95.2}

# Generate HTML
html_path = generate_html_report(pipeline_results, profile_results)
print(f"HTML Report: {html_path}")

# Generate Markdown
md_path = generate_markdown_report(pipeline_results, profile_results)
print(f"MD Report: {md_path}")
```

### Example 4: Pipeline History & Auditing

```python
from src.history import log_pipeline_run, get_pipeline_history, get_pipeline_stats

# Log a pipeline run
run_id = log_pipeline_run(
    status="success",
    samples=30,
    runs=48,
    qc=48,
    duration=12.5,
    input_dir="data/raw",
    output_dir="data/processed",
    mode="strict"
)

# Get history
history = get_pipeline_history(limit=10)
for run in history:
    print(f"Run {run['id']}: {run['status']} ({run['duration']:.2f}s)")

# Get statistics
stats = get_pipeline_stats()
print(f"Success Rate: {stats['success_rate']:.1f}%")
print(f"Total Samples: {stats['total_samples_processed']}")
```

### Example 5: Scheduled Execution

```python
from src.scheduler import create_etl_schedule, start_scheduler, stop_scheduler, list_schedules

# Create daily schedule
job_name = create_etl_schedule(interval=24, unit="hours")
print(f"Created schedule: {job_name}")

# Start scheduler
start_scheduler()
print("Scheduler started")

# List active jobs
schedules = list_schedules()
for name, info in schedules.items():
    print(f"  {name}: Every {info['interval']} {info['unit']}")

# Stop scheduler
# stop_scheduler()
```

### Example 6: QC Analysis (Genomics)

```python
from src.qc_metrics import analyze_qc_metrics, get_failed_samples

# Load QC data
qc_df = pd.read_csv("data/raw/qc_metrics.tsv", sep="\t")

# Analyze
analysis = analyze_qc_metrics(qc_df)
print(f"Q30 Pass Rate: {analysis['q30_stats']['pass_rate']:.1f}%")
print(f"GC Optimal Range: {analysis['gc_stats']['range_percentage']:.1f}%")

# Get failed samples
failed = get_failed_samples(qc_df)
print(f"Failed Samples: {len(failed['total_failed'])}")
```

### Example 7: Schema Inspection

```python
from src.schema_inspector import inspect_parquet_schema, compare_schemas

# Inspect Parquet
schema = inspect_parquet_schema(Path("data/processed/samples.parquet"))
print(f"Rows: {schema['num_rows']}")
print(f"Columns: {schema['num_columns']}")

# Compare schemas
csv_schema = inspect_csv_schema(Path("data/raw/samples.csv"))
parquet_schema = inspect_parquet_schema(Path("data/processed/dim_samples.parquet"))

comparison = compare_schemas(csv_schema, parquet_schema)
print(f"Common Columns: {len(comparison['common_columns'])}")
print(f"Type Changes: {comparison['type_changes']}")
```

### Example 8: File Upload & Batch Processing

```python
from src.file_upload import process_uploaded_file, batch_process_files

# Process single file
success, message, info = process_uploaded_file(
    uploaded_file,
    Path("data/raw_upload")
)

if success:
    print(f"Rows: {info['rows']}")
    print(f"Columns: {info['columns']}")

# Batch processing
files = list(Path("data/uploads").glob("*.csv"))
results = batch_process_files(files, process_func, Path("data/raw"))
print(f"Successful: {results['successful']}/{results['total']}")
```

---

## 🐛 Troubleshooting

### Problem: Port 8501 already in use

```bash
# Use different port
streamlit run app_advanced.py --server.port 8502
```

### Problem: ModuleNotFoundError for new modules

```bash
# Reinstall package
pip install -e ".[dev]"
pip install plotly schedule
```

### Problem: Permission denied on setup_advanced.sh

```bash
# Make executable
chmod +x setup_advanced.sh
bash setup_advanced.sh
```

### Problem: Data not loading in UI

```bash
# Check if data files exist
ls -la data/raw/
ls -la data/processed/

# If missing, run ETL first
python run_etl_new_data.py
```

### Problem: Scheduled jobs not running

```bash
# Check if scheduler is started
# In Python:
from src.scheduler import start_scheduler
start_scheduler()

# The scheduler runs in background threads
```

---

## 🚀 Production Deployment

### Option 1: Systemd Service (Linux)

Create `/etc/systemd/system/genomics-etl.service`:

```ini
[Unit]
Description=Genomics ETL Pipeline
After=network.target

[Service]
Type=simple
User=etl-user
WorkingDirectory=/opt/genomics-etl
ExecStart=/usr/bin/python -m streamlit run app_advanced.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable genomics-etl
sudo systemctl start genomics-etl
sudo systemctl status genomics-etl
```

### Option 2: Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - LOG_LEVEL=INFO
      - STREAMLIT_SERVER_HEADLESS=true
    restart: always

  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: genomics
      POSTGRES_USER: etl
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

Start:

```bash
docker-compose up -d
```

### Option 3: Kubernetes

```bash
# Create namespace
kubectl create namespace genomics

# Apply deployment
kubectl apply -f k8s/deployment.yaml -n genomics

# Check status
kubectl get pods -n genomics
kubectl logs -f deployment/genomics-etl -n genomics

# Port forward
kubectl port-forward svc/genomics-etl 8501:8501 -n genomics
```

### Option 4: Cloud Deployment (AWS)

```bash
# Build Docker image
docker build -t genomics-etl:latest .
docker tag genomics-etl:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/genomics-etl:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/genomics-etl:latest

# Deploy to ECS/EKS
aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs create-service --cluster genomics --service-name etl-service --task-definition genomics-etl --desired-count 2
```

---

## 📊 Monitoring

### View Logs

```bash
# Systemd
sudo journalctl -u genomics-etl -f

# Docker
docker logs -f genomics-etl

# Kubernetes
kubectl logs -f deployment/genomics-etl -n genomics
```

### Health Check

```bash
# Simple health check
curl http://localhost:8501

# With verbose output
curl -v http://localhost:8501
```

---

## 🔐 Security Best Practices

1. **Use environment variables** for sensitive data:
   ```bash
   export AWS_ACCESS_KEY_ID=xxx
   export AWS_SECRET_ACCESS_KEY=xxx
   ```

2. **Enable authentication** (optional Streamlit extension):
   ```bash
   pip install streamlit-authenticator
   ```

3. **Use HTTPS** in production:
   ```bash
   streamlit run app_advanced.py --logger.level=info --server.ssl.certfile=cert.pem --server.ssl.keyfile=key.pem
   ```

4. **Restrict file permissions**:
   ```bash
   chmod 600 .env
   chmod 700 data/
   ```

5. **Regular backups**:
   ```bash
   tar -czf backup_$(date +%Y%m%d).tar.gz data/ .streamlit/
   ```

---

## 📞 Support

For issues, questions, or feature requests:

- 📧 Email: support@genomics-etl.dev
- 🐛 GitHub Issues: [https://github.com/KamilJ117417/ETL-SQL-DuckDB-Parquet-/issues](https://github.com/KamilJ117417/ETL-SQL-DuckDB-Parquet-/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/KamilJ117417/ETL-SQL-DuckDB-Parquet-/discussions)

---

**Version**: 2.0  
**Last Updated**: January 20, 2026  
**Status**: ✅ Production Ready

