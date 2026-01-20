# Example Queries

This document contains detailed examples of SQL queries against the genomics metadata warehouse.

## Setup

First, load data:

```bash
python -m src.cli etl --input data/raw --output data/processed --mode strict
```

Then connect with DuckDB:

```python
import duckdb

conn = duckdb.connect(":memory:")

# Create views
conn.execute("CREATE VIEW samples AS SELECT * FROM read_parquet('data/processed/dim_samples.parquet')")
conn.execute("CREATE VIEW runs AS SELECT * FROM read_parquet('data/processed/fact_runs.parquet')")
conn.execute("CREATE VIEW qc_metrics AS SELECT * FROM read_parquet('data/processed/fact_qc_metrics.parquet')")
```

---

## Query 1: Project Overview

**What?** How many samples and runs per project?

**Use Case:** Project status dashboard

```sql
SELECT
  s.project_id,
  COUNT(DISTINCT s.sample_id) AS n_samples,
  COUNT(DISTINCT r.run_id)    AS n_runs,
  ROUND(SUM(r.fastq_gb), 2)   AS total_fastq_gb
FROM samples s
LEFT JOIN runs r USING(sample_id)
GROUP BY 1
ORDER BY n_runs DESC;
```

**Expected Output:**
```
project_id    n_samples  n_runs  total_fastq_gb
PRJNA001003   3          3       15.10
PRJNA001000   3          4       13.40
PRJNA001002   3          3       10.00
PRJNA001001   3          4       11.80
```

---

## Query 2: Low-Quality Runs

**What?** Which runs have the worst Q30 scores (highest error rate)?

**Use Case:** QC failure detection, troubleshooting

```sql
SELECT
  r.project_id,
  q.run_id,
  q.q30_rate,
  q.total_reads,
  r.fastq_gb
FROM qc_metrics q
JOIN runs r USING(run_id)
ORDER BY q.q30_rate ASC
LIMIT 10;
```

**Expected Output:**
```
project_id    run_id      q30_rate  total_reads  fastq_gb
PRJNA001001   SRR123008   0.75      72000000     2.1
PRJNA001002   SRR123007   0.87      118000000    4.0
PRJNA001002   SRR123003   0.88      145000000    5.0
PRJNA001001   SRR123005   0.89      112000000    3.8
```

---

## Query 3: Multi-Flag QC Status

**What?** Identify runs with multiple QC issues (low Q30 + high duplication + adapters)

**Use Case:** Prioritizing re-runs or troubleshooting

```sql
SELECT
  r.project_id,
  q.run_id,
  q.q30_rate,
  q.duplication_rate,
  q.adapter_content_flag,
  CASE
    WHEN q.q30_rate < 0.85 THEN 'LOW_Q30'
    WHEN q.duplication_rate > 0.6 THEN 'HIGH_DUP'
    WHEN q.adapter_content_flag THEN 'ADAPTERS'
    ELSE 'OK'
  END AS qc_status
FROM qc_metrics q
JOIN runs r USING(run_id)
ORDER BY q.q30_rate ASC;
```

**Expected Output:**
```
project_id    run_id      q30_rate  dup_rate  adapters  qc_status
PRJNA001001   SRR123008   0.75      0.42      true      LOW_Q30
PRJNA001001   SRR123004   0.78      0.35      true      LOW_Q30
PRJNA001002   SRR123003   0.88      0.22      true      ADAPTERS
...
```

---

## Query 4: Platform Comparison

**What?** How do different sequencing platforms compare in QC metrics?

**Use Case:** Platform validation, cost-benefit analysis

```sql
SELECT
  s.platform,
  COUNT(DISTINCT r.run_id) AS n_runs,
  ROUND(AVG(q.q30_rate), 3) AS avg_q30,
  ROUND(AVG(q.gc_percent), 1) AS avg_gc,
  ROUND(AVG(q.duplication_rate), 3) AS avg_dup,
  ROUND(MAX(q.total_reads), 0) AS max_reads
FROM qc_metrics q
JOIN runs r USING(run_id)
JOIN samples s USING(sample_id)
GROUP BY 1
ORDER BY avg_q30 DESC;
```

**Expected Output:**
```
platform      n_runs  avg_q30  avg_gc  avg_dup  max_reads
ILLUMINA      11      0.907    47.7    0.157    156000000
NANOPORE      2       0.765    51.5    0.385    85000000
```

---

## Query 5: Storage Analysis

**What?** Which projects consume most storage? (Cost implications)

**Use Case:** Budget forecasting, archival planning

```sql
SELECT
  r.project_id,
  COUNT(DISTINCT r.run_id) AS n_runs,
  ROUND(SUM(r.fastq_gb), 2) AS total_fastq_gb,
  ROUND(AVG(r.fastq_gb), 2) AS avg_fastq_gb_per_run
FROM runs r
GROUP BY 1
ORDER BY total_fastq_gb DESC;
```

**Expected Output:**
```
project_id    n_runs  total_fastq_gb  avg_per_run
PRJNA001003   3       15.10           5.03
PRJNA001000   4       13.40           3.35
PRJNA001001   4       11.80           2.95
PRJNA001002   3       10.00           3.33
```

---

## Query 6: Window Functions - Ranking

**What?** Rank runs within each project by Q30 (worst to best)

**Use Case:** Comparative analysis, identifying outliers

```sql
SELECT
  r.project_id,
  q.run_id,
  q.q30_rate,
  RANK() OVER (PARTITION BY r.project_id ORDER BY q.q30_rate ASC) AS rank_worst_q30,
  ROW_NUMBER() OVER (PARTITION BY r.project_id ORDER BY q.q30_rate DESC) AS rank_best_q30
FROM qc_metrics q
JOIN runs r USING(run_id)
ORDER BY r.project_id, rank_worst_q30;
```

**Key Concept:** RANK() partitions by project_id and ranks within each group independently.

**Expected Output:**
```
project_id    run_id      q30_rate  rank_worst  rank_best
PRJNA001000   SRR123003   0.88      1           4
PRJNA001000   SRR123002   0.91      2           3
PRJNA001000   SRR123001   0.92      3           2
PRJNA001000   SRR123002   0.91      4           1
PRJNA001001   SRR123004   0.78      1           4
...
```

---

## Query 7: Data Completeness

**What?** What percentage of critical fields are missing?

**Use Case:** Data quality metrics, SLA monitoring

```sql
SELECT
  'samples.sample_id' AS field,
  ROUND(100.0 * SUM(CASE WHEN sample_id IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS null_percent
FROM samples
UNION ALL
SELECT
  'runs.run_id',
  ROUND(100.0 * SUM(CASE WHEN run_id IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM runs
UNION ALL
SELECT
  'qc_metrics.q30_rate',
  ROUND(100.0 * SUM(CASE WHEN q30_rate IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM qc_metrics;
```

**Expected Output:**
```
field                  null_percent
samples.sample_id      0.00
runs.run_id            0.00
qc_metrics.q30_rate    0.00
```

---

## Query 8: Referential Integrity

**What?** Are there any runs without a corresponding sample? (FK violation)

**Use Case:** Data integrity audit

```sql
SELECT r.run_id, r.sample_id
FROM runs r
LEFT JOIN samples s USING(sample_id)
WHERE s.sample_id IS NULL
ORDER BY r.run_id;
```

**Expected Output (if all clean):**
```
(no rows)
```

---

## Query 9: Library Layout Distribution

**What?** Distribution of SINGLE vs PAIRED reads per project

**Use Case:** Experimental design review

```sql
SELECT
  s.project_id,
  r.library_layout,
  COUNT(DISTINCT r.run_id) AS n_runs,
  ROUND(100.0 * COUNT(DISTINCT r.run_id) / SUM(COUNT(DISTINCT r.run_id)) OVER (PARTITION BY s.project_id), 1) AS percent
FROM runs r
JOIN samples s USING(sample_id)
GROUP BY 1, 2
ORDER BY s.project_id, n_runs DESC;
```

**Expected Output:**
```
project_id    layout  n_runs  percent
PRJNA001000   PAIRED  4       100.0
PRJNA001001   PAIRED  4       100.0
PRJNA001002   PAIRED  2       66.7
PRJNA001002   SINGLE  1       33.3
...
```

---

## Query 10: Platform-Organism Matrix

**What?** Which organisms are sequenced on which platforms?

**Use Case:** Experiment metadata validation

```sql
SELECT
  s.organism,
  s.platform,
  COUNT(DISTINCT s.sample_id) AS n_samples,
  COUNT(DISTINCT r.run_id) AS n_runs,
  ROUND(SUM(r.fastq_gb), 2) AS total_fastq_gb
FROM samples s
LEFT JOIN runs r USING(sample_id)
GROUP BY 1, 2
ORDER BY s.organism, n_samples DESC;
```

**Expected Output:**
```
organism                  platform   n_samples  n_runs  total_gb
Arabidopsis thaliana      ILLUMINA   3          3       15.10
Caenorhabditis elegans    ILLUMINA   1          1       3.90
Homo sapiens              ILLUMINA   4          5       13.10
Homo sapiens              NANOPORE   1          1       2.30
Mus musculus              ILLUMINA   3          4       11.80
```

---

## Query 11: Tissue-Specific QC

**What?** How does tissue type affect sequencing quality?

**Use Case:** Tissue preprocessing optimization

```sql
SELECT
  s.tissue,
  COUNT(DISTINCT s.sample_id) AS n_samples,
  COUNT(DISTINCT r.run_id) AS n_runs,
  ROUND(AVG(q.q30_rate), 3) AS avg_q30,
  ROUND(AVG(q.duplication_rate), 3) AS avg_dup,
  SUM(CASE WHEN q.adapter_content_flag THEN 1 ELSE 0 END) AS n_with_adapters
FROM samples s
LEFT JOIN runs r USING(sample_id)
LEFT JOIN qc_metrics q USING(run_id)
GROUP BY 1
ORDER BY avg_q30 DESC;
```

**Expected Output:**
```
tissue          n_samples  n_runs  avg_q30  avg_dup  adapters
root            1          1       0.910    0.140    0
saliva          1          1       0.880    0.220    1
leaf            1          1       0.940    0.080    0
flower          1          1       0.890    0.190    1
...
```

---

## Query 12: Temporal Trends

**What?** Has QC improved over time?

**Use Case:** Process trending, improvement tracking

```sql
SELECT
  s.collection_date,
  COUNT(DISTINCT s.sample_id) AS n_samples,
  COUNT(DISTINCT r.run_id) AS n_runs,
  ROUND(AVG(q.q30_rate), 3) AS avg_q30
FROM samples s
LEFT JOIN runs r USING(sample_id)
LEFT JOIN qc_metrics q USING(run_id)
WHERE s.collection_date IS NOT NULL
GROUP BY 1
ORDER BY s.collection_date;
```

**Expected Output:**
```
collection_date  n_samples  n_runs  avg_q30
2024-01-15       1          2       0.915
2024-01-16       1          1       0.880
2024-01-17       1          1       0.880
2024-02-01       1          1       0.890
2024-02-02       1          1       0.930
2024-02-03       1          1       0.900
...
```

---

## Running Queries from CLI

```bash
# Run all queries and save results to markdown
python -m src.cli query \
  --parquet data/processed \
  --sql sql/queries.sql \
  --output docs/query_results.md
```

## Running Queries from Python

```python
import duckdb

conn = duckdb.connect(":memory:")
conn.execute("CREATE VIEW samples AS SELECT * FROM read_parquet('data/processed/dim_samples.parquet')")
conn.execute("CREATE VIEW runs AS SELECT * FROM read_parquet('data/processed/fact_runs.parquet')")
conn.execute("CREATE VIEW qc_metrics AS SELECT * FROM read_parquet('data/processed/fact_qc_metrics.parquet')")

result = conn.execute("""
  SELECT
    s.project_id,
    COUNT(DISTINCT s.sample_id) AS n_samples
  FROM samples s
  GROUP BY 1
""").fetchall()

print(result)
conn.close()
```
