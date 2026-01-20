"""
Streamlit GUI for Genomics Metadata ETL Pipeline
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import duckdb
from pathlib import Path
import logging
from typing import Optional
import time

from src.etl.ingest import ingest_all
from src.etl.validate import validate_all
from src.etl.transform import transform_all
from src.etl.load import load_to_processed
from src.benchmarks import run_benchmark

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="🧬 Genomics ETL Pipeline",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3em;
        color: #1f77b4;
        margin-bottom: 0.5em;
    }
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 15px;
        border-radius: 5px;
    }
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 15px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "pipeline_results" not in st.session_state:
    st.session_state.pipeline_results = None
if "query_results" not in st.session_state:
    st.session_state.query_results = None


def load_query_results():
    """Load Parquet files and return as views"""
    try:
        conn = duckdb.connect(":memory:")
        parquet_dir = Path("data/processed")
        
        tables = {
            "samples": "dim_samples.parquet",
            "runs": "fact_runs.parquet",
            "qc_metrics": "fact_qc_metrics.parquet"
        }
        
        for view_name, file_name in tables.items():
            parquet_path = parquet_dir / file_name
            if parquet_path.exists():
                conn.execute(
                    f"CREATE VIEW {view_name} AS SELECT * FROM read_parquet('{parquet_path}')"
                )
        
        return conn
    except Exception as e:
        st.error(f"❌ Błąd ładowania danych: {str(e)}")
        return None


# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Ustawienia")
    
    input_dir = st.text_input(
        "📁 Katalog wejściowy",
        value="data/raw",
        help="Ścieżka do plików CSV/TSV"
    )
    
    output_dir = st.text_input(
        "💾 Katalog wyjściowy",
        value="data/processed",
        help="Gdzie zapisać pliki Parquet"
    )
    
    mode = st.selectbox(
        "🎯 Tryb ETL",
        ["strict", "quarantine"],
        help="strict: Zatrzymaj na błędach | quarantine: Kontynuuj z poprawnymi"
    )
    
    log_level = st.selectbox(
        "📝 Poziom logowania",
        ["DEBUG", "INFO", "WARNING", "ERROR"],
        index=1
    )
    
    st.markdown("---")
    st.markdown("### ℹ️ Informacje")
    st.info(
        "🧬 **Genomics ETL Pipeline**\n\n"
        "Aplikacja do przetwarzania metadanych genomicznych.\n\n"
        "Funkcjonalności:\n"
        "- 📥 Wczytanie CSV/TSV\n"
        "- ✔️ Walidacja danych\n"
        "- 🔄 Transformacja schematu\n"
        "- 💾 Export do Parquet\n"
        "- 🔍 SQL queries\n"
        "- ⚡ Benchmark wydajności"
    )

# Main header
st.markdown('<div class="main-header">🧬 Genomics Metadata ETL Pipeline</div>', unsafe_allow_html=True)
st.markdown("**Profesjonalny pipeline ETL dla danych genomicznych**")
st.divider()

# Navigation
tab1, tab2, tab3, tab4 = st.tabs(
    ["🚀 Pipeline", "🔍 SQL Queries", "⚡ Benchmark", "📊 Wyniki"]
)

# ============================================================================
# TAB 1: PIPELINE
# ============================================================================
with tab1:
    st.header("🚀 Uruchom ETL Pipeline")
    st.markdown("""
    Pipeline wykonuje następujące kroki:
    1. **INGEST** — Wczytanie plików CSV/TSV
    2. **VALIDATE** — Sprawdzenie spójności danych
    3. **TRANSFORM** — Normalizacja i czyszczenie
    4. **LOAD** — Zapis do formatu Parquet
    """)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### Konfiguracja")
    
    with col2:
        st.markdown("### Akcje")
    
    # Run button
    if st.button("▶️ RUN ETL PIPELINE", key="run_pipeline", use_container_width=True):
        st.session_state.pipeline_results = None
        
        with st.spinner("⏳ Przetwarzanie..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.empty()
            
            try:
                # Step 1: Ingest
                status_text.info("📥 Krok 1/4: Wczytywanie danych...")
                progress_bar.progress(25)
                
                input_path = Path(input_dir)
                dfs = ingest_all(input_path)
                
                samples_count = len(dfs["samples"])
                runs_count = len(dfs["runs"])
                qc_count = len(dfs["qc_metrics"])
                
                # Step 2: Validate
                status_text.info("✔️ Krok 2/4: Walidacja danych...")
                progress_bar.progress(50)
                
                is_valid, errors = validate_all(
                    dfs["samples"],
                    dfs["runs"],
                    dfs["qc_metrics"],
                    mode=mode
                )
                
                validation_status = "✅ PASSED" if is_valid else f"⚠️ {len(errors)} błędów"
                
                # Step 3: Transform
                status_text.info("🔄 Krok 3/4: Transformacja danych...")
                progress_bar.progress(75)
                
                transformed = transform_all(
                    dfs["samples"],
                    dfs["runs"],
                    dfs["qc_metrics"]
                )
                
                # Step 4: Load
                status_text.info("💾 Krok 4/4: Zapis Parquet...")
                progress_bar.progress(90)
                
                output_path = Path(output_dir)
                load_to_processed(
                    transformed["samples"],
                    transformed["runs"],
                    transformed["qc_metrics"],
                    output_path
                )
                
                progress_bar.progress(100)
                
                # Store results
                st.session_state.pipeline_results = {
                    "success": True,
                    "samples": samples_count,
                    "runs": runs_count,
                    "qc_metrics": qc_count,
                    "validation": validation_status,
                    "errors": errors[:5] if errors else []
                }
                
                # Display success
                status_text.empty()
                progress_bar.empty()
                
                st.success("✅ Pipeline ukończony pomyślnie!")
                
                # Results summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📊 Samples", samples_count)
                with col2:
                    st.metric("🏃 Runs", runs_count)
                with col3:
                    st.metric("📈 QC Metrics", qc_count)
                
                # Validation status
                st.markdown("### Wyniki Walidacji")
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Status**: {validation_status}")
                if errors:
                    with st.expander("👁️ Pokaż błędy"):
                        for i, error in enumerate(errors[:5], 1):
                            st.warning(f"{i}. {error}")
                
                # Output files
                st.markdown("### 📁 Wygenerowane pliki")
                output_files = list(Path(output_dir).glob("*.parquet"))
                if output_files:
                    file_data = []
                    for f in output_files:
                        size_mb = f.stat().st_size / (1024 * 1024)
                        file_data.append({
                            "Plik": f.name,
                            "Rozmiar": f"{size_mb:.2f} MB",
                            "Data": pd.Timestamp(f.stat().st_mtime, unit='s')
                        })
                    df_files = pd.DataFrame(file_data)
                    st.dataframe(df_files, use_container_width=True)
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Błąd: {str(e)}")
                st.session_state.pipeline_results = {"success": False, "error": str(e)}

# ============================================================================
# TAB 2: SQL QUERIES
# ============================================================================
with tab2:
    st.header("🔍 SQL Queries")
    st.markdown("Wykonuj zapytania SQL na wczytanych danych Parquet")
    
    # Load data
    conn = load_query_results()
    
    if conn is None:
        st.warning("⚠️ Brak danych. Uruchom najpierw pipeline!")
    else:
        # Query type selection
        query_type = st.radio(
            "Typ zapytania",
            ["Predefiniowane", "Custom"],
            horizontal=True
        )
        
        if query_type == "Predefiniowane":
            st.markdown("### Szablonowe zapytania")
            
            query_templates = {
                "Liczba próbek": "SELECT COUNT(*) as liczba FROM samples",
                "Liczba runów": "SELECT COUNT(*) as liczba FROM runs",
                "Top 5 największych runów": 
                    "SELECT run_id, fastq_gb FROM runs ORDER BY fastq_gb DESC LIMIT 5",
                "Średnia Q30 na platformę":
                    "SELECT s.platform, AVG(q.q30_rate) as avg_q30 FROM qc_metrics q "
                    "JOIN runs r USING(run_id) JOIN samples s USING(sample_id) "
                    "GROUP BY s.platform",
                "Rozkład QC metrics":
                    "SELECT COUNT(*) as count, "
                    "ROUND(q30_rate, 1) as q30_bin FROM qc_metrics "
                    "GROUP BY ROUND(q30_rate, 1) ORDER BY q30_bin DESC"
            }
            
            selected_query = st.selectbox(
                "Wybierz zapytanie",
                list(query_templates.keys())
            )
            
            query = query_templates[selected_query]
            
        else:
            st.markdown("### Custom SQL Query")
            query = st.text_area(
                "Napisz zapytanie SQL",
                value="SELECT * FROM samples LIMIT 5",
                height=150
            )
        
        # Execute query
        if st.button("▶️ Wykonaj zapytanie", use_container_width=True):
            try:
                with st.spinner("⏳ Wykonywanie..."):
                    result = conn.execute(query).fetchall()
                    columns = [desc[0] for desc in conn.description]
                    
                    df_result = pd.DataFrame(result, columns=columns)
                    
                    st.success(f"✅ Zapytanie wykonane ({len(df_result)} wierszy)")
                    st.dataframe(df_result, use_container_width=True)
                    
                    # Download button
                    csv = df_result.to_csv(index=False)
                    st.download_button(
                        "⬇️ Pobierz jako CSV",
                        csv,
                        "query_results.csv",
                        "text/csv"
                    )
            except Exception as e:
                st.error(f"❌ Błąd zapytania: {str(e)}")

# ============================================================================
# TAB 3: BENCHMARK
# ============================================================================
with tab3:
    st.header("⚡ Benchmark")
    st.markdown("Porównaj wydajność CSV vs Parquet")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_file = st.text_input(
            "📄 Plik CSV",
            value="data/raw/runs.csv"
        )
    
    with col2:
        parquet_file = st.text_input(
            "📦 Plik Parquet",
            value="data/processed/fact_runs.parquet"
        )
    
    if st.button("▶️ RUN BENCHMARK", use_container_width=True):
        try:
            with st.spinner("⏳ Wykonywanie benchmarku..."):
                results = run_benchmark(Path(csv_file), Path(parquet_file))
                
                st.success("✅ Benchmark ukończony")
                
                # Display results
                st.markdown("### 📊 Wyniki")
                st.markdown(results)
                
                # Download results
                st.download_button(
                    "⬇️ Pobierz raport",
                    results,
                    "benchmark_results.md",
                    "text/markdown"
                )
        except Exception as e:
            st.error(f"❌ Błąd: {str(e)}")

# ============================================================================
# TAB 4: RESULTS
# ============================================================================
with tab4:
    st.header("📊 Wyniki")
    
    if st.session_state.pipeline_results is None:
        st.info("📋 Brak wyników. Uruchom najpierw pipeline!")
    else:
        results = st.session_state.pipeline_results
        
        if results.get("success"):
            st.markdown("### ✅ Pipeline zaraz się powiódł")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Samples", results["samples"])
            with col2:
                st.metric("Runs", results["runs"])
            with col3:
                st.metric("QC Metrics", results["qc_metrics"])
            
            st.markdown("### Walidacja")
            st.write(f"Status: **{results['validation']}**")
            
            if results.get("errors"):
                with st.expander("Błędy"):
                    for error in results["errors"]:
                        st.error(error)
        else:
            st.error(f"❌ Pipeline nie powiódł się: {results.get('error')}")
    
    # Show data preview
    st.markdown("### 👁️ Podgląd danych")
    
    conn = load_query_results()
    if conn:
        table_choice = st.selectbox(
            "Wybierz tabelę",
            ["samples", "runs", "qc_metrics"]
        )
        
        try:
            df = conn.execute(f"SELECT * FROM {table_choice} LIMIT 10").df()
            st.dataframe(df, use_container_width=True)
            
            # Stats
            row_count = conn.execute(f"SELECT COUNT(*) FROM {table_choice}").fetchall()[0][0]
            st.info(f"📊 Razem wierszy: **{row_count}**")
        except Exception as e:
            st.error(f"Błąd: {str(e)}")

# Footer
st.divider()
st.markdown(
    "---\n"
    "🧬 **Genomics ETL Pipeline** | "
    "[GitHub](https://github.com/KamilJ117417/ETL-SQL-DuckDB-Parquet-) | "
    "v0.1.0"
)
