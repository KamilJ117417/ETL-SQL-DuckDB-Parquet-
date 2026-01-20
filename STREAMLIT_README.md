# 🧬 Streamlit GUI — Genomics ETL Pipeline

## 🚀 Uruchomienie

### Opcja 1: Lokalnie

```bash
# Zainstaluj zależności
pip install streamlit

# Uruchom aplikację
streamlit run app.py
```

Aplikacja otworzy się w przeglądarce: **http://localhost:8501**

### Opcja 2: Zdalne (dev container)

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 📋 Funkcjonalności

### 1️⃣ **Pipeline** — Uruchom ETL

- 📥 Wczytaj pliki CSV/TSV
- ✔️ Waliduj dane
- 🔄 Transformuj schemat
- 💾 Eksportuj do Parquet
- 📊 Wyświetl metryki

**Parametry**:
- `Input directory` — Katalog z danymi raw (default: `data/raw`)
- `Output directory` — Gdzie zapisać Parquet (default: `data/processed`)
- `Mode` — `strict` (stop na błędzie) lub `quarantine` (kontynuuj)
- `Log level` — DEBUG/INFO/WARNING/ERROR

### 2️⃣ **SQL Queries** — Zapytania na danych

**Predefiniowane**:
- Liczba próbek
- Liczba runów
- Top 5 największych runów
- Średnia Q30 na platformę
- Rozkład QC metrics

**Custom**: Napisz własne SQL query

**Funkcjonalności**:
- ✅ Execute query
- 📥 Pobierz wyniki (CSV)
- 📊 Wyświetl tabele

### 3️⃣ **Benchmark** — Porównaj wydajność

- CSV vs Parquet performance
- Rozmiar plików
- Query speed
- 📥 Pobierz raport (MD)

### 4️⃣ **Wyniki** — Historia i podgląd

- Podsumowanie ostatniego pipeline
- Podgląd danych (10 wierszy)
- Statystyki tabel

---

## 🎨 Interfejs

```
┌─────────────────────────────────────────────────────┐
│         🧬 Genomics Metadata ETL Pipeline           │
│                                                      │
│  [🚀 Pipeline] [🔍 SQL Queries] [⚡ Benchmark] [📊 Results]
│                                                      │
│  ▶️ RUN ETL PIPELINE                               │
│                                                      │
│  📊 Samples: 30  |  Runs: 48  |  QC: 48            │
│  ✅ Validation: PASSED                              │
│  📁 Wygenerowane pliki: 3                           │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 💾 Dane wejściowe

Aplikacja oczekuje danych w `data/raw/`:

```
data/raw/
├── samples.csv          (30 wierszy)
├── runs.csv             (48 wierszy)
└── qc_metrics.tsv       (48 wierszy)
```

---

## 📤 Wyjście

Parquet files w `data/processed/`:

```
data/processed/
├── dim_samples.parquet        (30 wierszy)
├── fact_runs.parquet          (48 wierszy)
└── fact_qc_metrics.parquet    (48 wierszy)
```

---

## ⚙️ Konfiguracja

Edytuj `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1f77b4"        # Kolor główny
backgroundColor = "#ffffff"     # Tło
font = "sans serif"             # Font

[server]
port = 8501                     # Port aplikacji
headless = true                 # Bez GUI
runOnSave = true                # Reload na Save
```

---

## 🐛 Troubleshooting

**Problem**: `ModuleNotFoundError: No module named 'streamlit'`

```bash
pip install streamlit
```

**Problem**: Port 8501 jest zajęty

```bash
streamlit run app.py --server.port 8502
```

**Problem**: Brak danych w `data/processed/`

```bash
# Uruchom ETL pipeline najpierw
python run_etl_new_data.py
```

---

## 📊 Przykłady queries

### Query 1: Statystyki ogólne
```sql
SELECT 
  COUNT(*) as samples,
  COUNT(DISTINCT project_id) as projects,
  COUNT(DISTINCT platform) as platforms
FROM samples
```

### Query 2: Top runs by size
```sql
SELECT 
  run_id,
  sample_id,
  fastq_gb,
  library_layout
FROM runs
ORDER BY fastq_gb DESC
LIMIT 10
```

### Query 3: Quality metrics
```sql
SELECT 
  s.platform,
  AVG(q.q30_rate) as avg_q30,
  AVG(q.gc_percent) as avg_gc,
  COUNT(*) as count
FROM qc_metrics q
JOIN runs r USING(run_id)
JOIN samples s USING(sample_id)
GROUP BY s.platform
ORDER BY avg_q30 DESC
```

---

## 🚀 Production Deployment

### Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .
RUN pip install -e .[dev]

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

```bash
docker build -t etl-gui .
docker run -p 8501:8501 -v $(pwd)/data:/app/data etl-gui
```

### Systemd Service (Linux)

```ini
[Unit]
Description=Genomics ETL GUI
After=network.target

[Service]
Type=simple
User=etl
WorkingDirectory=/opt/etl
ExecStart=/usr/bin/python -m streamlit run app.py --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 📝 Notatki

- ✅ GUI jest w pełni funkcjonalne
- ✅ Obsługuje zarówno predefiniowane jak i custom queries
- ✅ Real-time progress bar
- ✅ Download results
- ✅ Responsive design

---

**Autor**: GitHub Copilot  
**Wersja**: 0.1.0  
**Status**: ✅ Production Ready
