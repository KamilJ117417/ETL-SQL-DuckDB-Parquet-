"""
🧬 Genomics ETL Pipeline - Advanced Streamlit GUI
Run with: streamlit run app_advanced.py
"""

import streamlit as st
import pandas as pd
import duckdb
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta
import logging
import time

# Import all new modules
from src.etl.ingest import ingest_all
from src.etl.validate import validate_all
from src.etl.transform import transform_all
from src.etl.load import load_to_processed
from src.benchmarks import run_benchmark
from src.profiling import profile_dataframe, data_quality_report, compare_dataframes
from src.reporting import generate_html_report, generate_markdown_report
from src.history import log_pipeline_run, get_pipeline_history, get_pipeline_stats, log_event, export_history
from src.scheduler import create_etl_schedule, list_schedules, cancel_schedule, start_scheduler, stop_scheduler
from src.schema_inspector import inspect_parquet_schema, inspect_csv_schema, compare_schemas, generate_schema_report
from src.file_upload import validate_file, process_uploaded_file, batch_process_files
from src.qc_metrics import analyze_qc_metrics, get_failed_samples, generate_qc_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="🧬 Genomics ETL Pipeline - Advanced",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 3em; color: #1f77b4; margin-bottom: 0.5em; }
    .metric-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; 
                  padding: 20px; border-radius: 10px; text-align: center; }
    .success-box { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; 
                   padding: 15px; border-radius: 5px; }
    .warning-box { background: #fff3cd; border: 1px solid #ffc107; color: #856404; 
                   padding: 15px; border-radius: 5px; }
    .error-box { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; 
                 padding: 15px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "pipeline_results" not in st.session_state:
    st.session_state.pipeline_results = None
if "pipeline_id" not in st.session_state:
    st.session_state.pipeline_id = None
if "query_results" not in st.session_state:
    st.session_state.query_results = None

def load_query_results():
    """Load Parquet files as DuckDB views"""
    try:
        conn = duckdb.connect(":memory:")
        parquet_dir = Path("data/processed")
        
        tables = {"samples": "dim_samples.parquet", "runs": "fact_runs.parquet", "qc_metrics": "fact_qc_metrics.parquet"}
        
        for view_name, file_name in tables.items():
            parquet_path = parquet_dir / file_name
            if parquet_path.exists():
                conn.execute(f"CREATE VIEW {view_name} AS SELECT * FROM read_parquet('{parquet_path}')")
        
        return conn
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return None

# SIDEBAR
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    input_dir = st.text_input("📁 Input Directory", "data/raw")
    output_dir = st.text_input("💾 Output Directory", "data/processed")
    mode = st.selectbox("🎯 Mode", ["strict", "quarantine"])
    
    st.divider()
    st.markdown("### ℹ️ About")
    st.info("🧬 **Genomics ETL Pipeline v2.0**\n\nAdvanced features for genomics data processing with profiling, reporting, scheduling & more!")

# Main header
st.markdown('<div class="main-header">🧬 Genomics Metadata ETL Pipeline</div>', unsafe_allow_html=True)
st.markdown("**Advanced Edition - Data Profiling, Reporting, Quality Metrics & More**")
st.divider()

# Navigation tabs
tabs = st.tabs([
    "🚀 Pipeline",
    "📊 Data Profiling",
    "📈 QC Metrics",
    "🔍 SQL Queries",
    "⚡ Benchmark",
    "🔄 Comparison",
    "📋 Schema",
    "📁 Upload",
    "📄 Reports",
    "📅 Scheduling",
    "🕐 History"
])

# ============================================================================
# TAB 1: PIPELINE
# ============================================================================
with tabs[0]:
    st.header("🚀 Run ETL Pipeline")
    st.markdown("Execute the complete ETL process: INGEST → VALIDATE → TRANSFORM → LOAD")
    
    if st.button("▶️ RUN ETL PIPELINE", key="run_pipeline", use_container_width=True):
        with st.spinner("⏳ Processing..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            start_time = time.time()
            try:
                # Step 1: Ingest
                status_text.info("📥 Step 1/4: Ingesting...")
                progress_bar.progress(25)
                input_path = Path(input_dir)
                dfs = ingest_all(input_path)
                
                # Step 2: Validate
                status_text.info("✔️ Step 2/4: Validating...")
                progress_bar.progress(50)
                is_valid, errors = validate_all(dfs["samples"], dfs["runs"], dfs["qc_metrics"], mode=mode)
                
                # Step 3: Transform
                status_text.info("🔄 Step 3/4: Transforming...")
                progress_bar.progress(75)
                transformed = transform_all(dfs["samples"], dfs["runs"], dfs["qc_metrics"])
                
                # Step 4: Load
                status_text.info("💾 Step 4/4: Loading...")
                progress_bar.progress(90)
                output_path = Path(output_dir)
                load_to_processed(transformed["samples"], transformed["runs"], transformed["qc_metrics"], output_path)
                
                # Log to history
                duration = time.time() - start_time
                pipeline_id = log_pipeline_run(
                    status="success",
                    samples=len(dfs["samples"]),
                    runs=len(dfs["runs"]),
                    qc=len(dfs["qc_metrics"]),
                    duration=duration,
                    input_dir=input_dir,
                    output_dir=output_dir,
                    mode=mode,
                    errors=errors if not is_valid else None
                )
                
                st.session_state.pipeline_results = {
                    "success": True,
                    "samples": len(dfs["samples"]),
                    "runs": len(dfs["runs"]),
                    "qc_metrics": len(dfs["qc_metrics"]),
                    "duration": duration,
                    "validation": "✅ PASSED" if is_valid else f"⚠️ {len(errors)} errors",
                    "errors": errors[:5] if errors else []
                }
                st.session_state.pipeline_id = pipeline_id
                
                progress_bar.progress(100)
                status_text.empty()
                progress_bar.empty()
                
                st.success(f"✅ Pipeline completed in {duration:.2f}s!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Samples", len(dfs["samples"]))
                with col2:
                    st.metric("🏃 Runs", len(dfs["runs"]))
                with col3:
                    st.metric("📈 QC Metrics", len(dfs["qc_metrics"]))
                
                st.markdown("### Validation Status")
                st.write(st.session_state.pipeline_results["validation"])
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 2: DATA PROFILING
# ============================================================================
with tabs[1]:
    st.header("📊 Data Profiling")
    st.markdown("Comprehensive data quality analysis and statistics")
    
    if st.button("🔍 ANALYZE DATA", use_container_width=True):
        try:
            conn = load_query_results()
            if conn:
                # Get samples data
                samples_df = conn.execute("SELECT * FROM samples").df()
                
                # Profile
                profile = profile_dataframe(samples_df)
                quality = data_quality_report(samples_df)
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Quality Score", f"{quality['quality_score']:.1f}%")
                with col2:
                    st.metric("Complete Records", quality['total_rows'] - quality['missing_cells']//len(samples_df.columns))
                with col3:
                    st.metric("Duplicates", quality['duplicate_rows'])
                with col4:
                    st.metric("Columns", quality['total_columns'])
                
                # Column analysis
                st.markdown("### 📋 Column Statistics")
                col_data = []
                for col, stats in quality['column_quality'].items():
                    col_data.append({
                        "Column": col,
                        "Completeness": f"{stats['completeness']:.1f}%",
                        "Missing": stats['missing'],
                        "Unique": stats['unique']
                    })
                
                st.dataframe(pd.DataFrame(col_data), use_container_width=True)
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ============================================================================
# TAB 3: QC METRICS
# ============================================================================
with tabs[2]:
    st.header("📈 Quality Control Metrics")
    st.markdown("Genomics-specific QC analysis")
    
    try:
        conn = load_query_results()
        if conn:
            qc_df = conn.execute("SELECT * FROM qc_metrics").df()
            
            if len(qc_df) > 0:
                # Analyze
                analysis = analyze_qc_metrics(qc_df)
                
                # Overall score
                quality_score = analysis['summary']['overall_quality_score']
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric("Quality Score", f"{quality_score:.1f}/100")
                with col2:
                    st.progress(quality_score / 100)
                
                # Metrics by type
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### Q30 Rate")
                    if analysis['q30_stats']:
                        st.metric("Pass Rate", f"{analysis['q30_stats'].get('pass_rate', 0):.1f}%")
                        st.metric("Mean", f"{analysis['q30_stats'].get('mean', 0):.1f}%")
                
                with col2:
                    st.markdown("### GC Content")
                    if analysis['gc_stats']:
                        st.metric("In Range", f"{analysis['gc_stats'].get('range_percentage', 0):.1f}%")
                        st.metric("Mean", f"{analysis['gc_stats'].get('mean', 0):.1f}%")
                
                with col3:
                    st.markdown("### Duplication")
                    if analysis['duplication_stats']:
                        st.metric("High Rate %", f"{analysis['duplication_stats'].get('high_dup_rate', 0):.1f}%")
                        st.metric("Mean", f"{analysis['duplication_stats'].get('mean', 0):.1f}%")
                
                # Failed samples
                failed = get_failed_samples(qc_df)
                if failed['total_failed']:
                    st.warning(f"⚠️ {len(failed['total_failed'])} samples failed QC thresholds")
                    with st.expander("View Failed Samples"):
                        st.write(failed['total_failed'])
                
                # Report
                st.markdown("### 📋 QC Report")
                report = generate_qc_report(qc_df)
                st.code(report, language="text")
                
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ============================================================================
# TAB 4: SQL QUERIES
# ============================================================================
with tabs[3]:
    st.header("🔍 SQL Queries")
    
    query_type = st.radio("Type", ["Predefin", "Custom"], horizontal=True)
    
    conn = load_query_results()
    if conn:
        if query_type == "Predefin":
            templates = {
                "Count": "SELECT COUNT(*) as count FROM samples",
                "Top 5 Runs": "SELECT run_id, fastq_gb FROM runs ORDER BY fastq_gb DESC LIMIT 5",
                "Avg Q30": "SELECT s.platform, AVG(q.q30_rate) FROM qc_metrics q JOIN runs r USING(run_id) JOIN samples s USING(sample_id) GROUP BY s.platform"
            }
            selected = st.selectbox("Query", list(templates.keys()))
            query = templates[selected]
        else:
            query = st.text_area("SQL", "SELECT * FROM samples LIMIT 5", height=150)
        
        if st.button("▶️ Execute", use_container_width=True):
            try:
                result = conn.execute(query).fetchall()
                columns = [desc[0] for desc in conn.description]
                df_result = pd.DataFrame(result, columns=columns)
                st.dataframe(df_result, use_container_width=True)
                
                csv = df_result.to_csv(index=False)
                st.download_button("⬇️ CSV", csv, "results.csv", "text/csv")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ============================================================================
# TAB 5: BENCHMARK
# ============================================================================
with tabs[4]:
    st.header("⚡ Benchmark")
    
    col1, col2 = st.columns(2)
    with col1:
        csv_file = st.text_input("CSV", "data/raw/runs.csv")
    with col2:
        parquet_file = st.text_input("Parquet", "data/processed/fact_runs.parquet")
    
    if st.button("▶️ RUN", use_container_width=True):
        try:
            with st.spinner("Running benchmark..."):
                results = run_benchmark(Path(csv_file), Path(parquet_file))
                st.markdown(results)
                st.download_button("⬇️ Report", results, "benchmark.md", "text/markdown")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ============================================================================
# TAB 6: DATA COMPARISON
# ============================================================================
with tabs[5]:
    st.header("🔄 Before/After Comparison")
    
    try:
        conn = load_query_results()
        if conn:
            samples_df = conn.execute("SELECT * FROM samples").df()
            
            if st.button("📊 COMPARE", use_container_width=True):
                # Simple comparison: count changes
                st.markdown("### Data Changes")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rows", len(samples_df))
                with col2:
                    st.metric("Columns", len(samples_df.columns))
                with col3:
                    st.metric("Memory", f"{samples_df.memory_usage(deep=True).sum() / (1024*1024):.2f} MB")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ============================================================================
# TAB 7: SCHEMA INSPECTOR
# ============================================================================
with tabs[6]:
    st.header("📋 Schema Inspector")
    
    schema_type = st.radio("Type", ["Parquet", "CSV"], horizontal=True)
    
    if schema_type == "Parquet":
        pq_path = st.text_input("File", "data/processed/dim_samples.parquet")
        if st.button("🔍 Inspect"):
            try:
                schema = inspect_parquet_schema(Path(pq_path))
                st.json(schema)
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        csv_path = st.text_input("File", "data/raw/samples.csv")
        if st.button("🔍 Inspect"):
            try:
                schema = inspect_csv_schema(Path(csv_path))
                st.json(schema)
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ============================================================================
# TAB 8: FILE UPLOAD
# ============================================================================
with tabs[7]:
    st.header("📁 Multi-File Upload")
    
    uploaded_files = st.file_uploader("Upload CSV/TSV files", accept_multiple_files=True, type=['csv', 'tsv'])
    
    if uploaded_files and st.button("▶️ PROCESS"):
        target_dir = Path("data/raw_upload")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for uploaded_file in uploaded_files:
            success, message, info = process_uploaded_file(uploaded_file, target_dir)
            if success:
                st.success(f"✅ {uploaded_file.name}: {info['rows']} rows")
            else:
                st.error(f"❌ {uploaded_file.name}: {message}")

# ============================================================================
# TAB 9: REPORTS
# ============================================================================
with tabs[8]:
    st.header("📄 Report Generation")
    
    report_type = st.selectbox("Type", ["HTML", "Markdown"])
    
    if st.button("📋 GENERATE"):
        if st.session_state.pipeline_results:
            try:
                conn = load_query_results()
                if conn:
                    samples_df = conn.execute("SELECT * FROM samples").df()
                    profile = profile_dataframe(samples_df)
                    quality = data_quality_report(samples_df)
                    
                    if report_type == "HTML":
                        path = generate_html_report(st.session_state.pipeline_results, quality)
                    else:
                        path = generate_markdown_report(st.session_state.pipeline_results, quality)
                    
                    st.success(f"✅ Report saved: {path}")
                    with open(path, 'r') as f:
                        st.download_button("⬇️ Download", f.read(), f"{report_type.lower()}_report", f"text/{report_type.lower()}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Run pipeline first!")

# ============================================================================
# TAB 10: SCHEDULING
# ============================================================================
with tabs[9]:
    st.header("📅 Pipeline Scheduling")
    
    col1, col2 = st.columns(2)
    with col1:
        interval = st.number_input("Interval", 1, 24, 1)
    with col2:
        unit = st.selectbox("Unit", ["minutes", "hours", "days"])
    
    if st.button("⏱️ CREATE SCHEDULE"):
        try:
            job_name = create_etl_schedule(interval, unit)
            st.success(f"✅ Scheduled: {job_name}")
            start_scheduler()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    # List jobs
    schedules = list_schedules()
    if schedules:
        st.markdown("### Active Schedules")
        for name, info in schedules.items():
            st.write(f"📌 {name}: Every {info['interval']} {info['unit']}")

# ============================================================================
# TAB 11: HISTORY
# ============================================================================
with tabs[10]:
    st.header("🕐 Pipeline History")
    
    stats = get_pipeline_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Runs", stats['total_runs'])
    with col2:
        st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
    with col3:
        st.metric("Failed", stats['failed_runs'])
    with col4:
        st.metric("Total Duration", f"{stats['total_duration_seconds']/3600:.1f}h")
    
    # History table
    history = get_pipeline_history(limit=20)
    if history:
        df_history = pd.DataFrame(history)
        st.dataframe(df_history, use_container_width=True)
        
        if st.button("📤 EXPORT"):
            path = export_history()
            st.success(f"✅ Exported: {path}")
    else:
        st.info("No history yet")

# Footer
st.divider()
st.markdown("---\n🧬 **Genomics ETL Pipeline v2.0** | [GitHub](https://github.com/KamilJ117417/ETL-SQL-DuckDB-Parquet-)")
