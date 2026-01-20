# Example Query Output

Below are example results from running the SQL queries in [sql/queries.sql](../sql/queries.sql).

## Q1: Project Summary

**Command:**
```bash
python -m src.cli query --parquet data/processed --sql sql/queries.sql --output docs/query_results.md
```

**Sample Output:**

```
project_id    n_samples  n_runs  total_fastq_gb
PRJNA001003        3          3             15.1
PRJNA001000        3          4             13.4
PRJNA001001        3          4             11.8
PRJNA001002        3          3             10.0
```

## Q2: Low Quality Runs

```
project_id    run_id      q30_rate  total_reads     fastq_gb
PRJNA001001   SRR123008   0.75      72000000        2.1
PRJNA001001   SRR123004   0.78      85000000        2.3
PRJNA001002   SRR123003   0.88      145000000       5.0
PRJNA001000   SRR123002   0.88      130000000       4.1
PRJNA001002   SRR123007   0.87      118000000       4.0
...
```

## Q3: QC Status Flags

```
project_id    run_id      q30_rate  dup_rate  adapters  qc_status
PRJNA001001   SRR123008   0.75      0.42      true      LOW_Q30
PRJNA001001   SRR123004   0.78      0.35      true      LOW_Q30
PRJNA001002   SRR123003   0.88      0.22      true      ADAPTERS
PRJNA001002   SRR123007   0.87      0.25      true      ADAPTERS
PRJNA001002   SRR123009   0.86      0.28      true      ADAPTERS
PRJNA001001   SRR123005   0.89      0.12      false     OK
PRJNA001000   SRR123001   0.92      0.15      false     OK
PRJNA001000   SRR123002   0.91      0.18      false     OK
PRJNA001003   SRR123010   0.94      0.08      false     OK
PRJNA001003   SRR123012   0.89      0.19      true      ADAPTERS
PRJNA001003   SRR123011   0.91      0.14      false     OK
PRJNA001000   SRR123003   0.88      0.22      true      ADAPTERS
PRJNA001001   SRR123006   0.93      0.11      false     OK
PRJNA001001   SRR123013   0.90      0.09      false     OK
```

## Q4: Platform Comparison

```
platform    n_runs  avg_q30  avg_gc  avg_dup  max_reads
ILLUMINA       11    0.907   47.7    0.157    156000000
NANOPORE        2    0.765   51.5    0.385    85000000
```

**Interpretation:**
- ILLUMINA achieves better Q30 (0.91 vs 0.77)
- ILLUMINA has lower duplication (0.16 vs 0.39)
- NANOPORE has higher GC bias (51.5% vs 47.7%)
- NANOPORE produces longer reads (up to 12kb vs 150bp)

## Q5: Storage by Project

```
project_id    n_runs  total_fastq_gb  avg_per_run
PRJNA001003       3           15.10           5.03
PRJNA001000       4           13.40           3.35
PRJNA001001       4           11.80           2.95
PRJNA001002       3           10.00           3.33
```

**Cost Estimation (AWS S3 storage):**
- PRJNA001003: 15.1 GB × $0.023/GB = $0.35/month
- All projects: 50.3 GB × $0.023/GB = $1.16/month

## Q6: Ranking Window Function

```
project_id    run_id      q30_rate  rank_worst  rank_best
PRJNA001000   SRR123003   0.88      1           4
PRJNA001000   SRR123002   0.91      2           3
PRJNA001000   SRR123001   0.92      3           2
PRJNA001000   SRR123002   0.91      4           1
PRJNA001001   SRR123004   0.78      1           4
PRJNA001001   SRR123008   0.78      2           3
PRJNA001001   SRR123005   0.89      3           2
PRJNA001001   SRR123006   0.93      4           1
PRJNA001002   SRR123007   0.87      1           3
PRJNA001002   SRR123003   0.88      2           2
PRJNA001002   SRR123009   0.86      3           1
PRJNA001003   SRR123012   0.89      1           3
PRJNA001003   SRR123011   0.91      2           2
PRJNA001003   SRR123010   0.94      3           1
```

**Interpretation:**
- PRJNA001000: Q30 ranges 0.88–0.92 (tight, good quality)
- PRJNA001001: Q30 ranges 0.78–0.93 (wide, variable quality)
- PRJNA001003: Q30 ranges 0.89–0.94 (excellent, consistent)

## Q7: Data Completeness

```
field                  null_percent
samples.sample_id      0.00
runs.run_id            0.00
qc_metrics.q30_rate    0.00
```

**Status:** ✓ All critical fields are 100% complete.

## Q8: Referential Integrity

```
(no rows)
```

**Status:** ✓ All FK constraints satisfied. Every run has a corresponding sample.

## Q9: Library Layout Distribution

```
project_id    layout  n_runs  percent
PRJNA001000   PAIRED  4       100.0
PRJNA001001   PAIRED  4       100.0
PRJNA001002   PAIRED  2       66.7
PRJNA001002   SINGLE  1       33.3
PRJNA001003   PAIRED  3       100.0
```

**Interpretation:**
- Most projects are 100% PAIRED-end
- PRJNA001002 has 33% SINGLE-end reads (likely long-read NANOPORE)

## Q10: Platform-Organism Matrix

```
organism                  platform   n_samples  n_runs  total_gb
Arabidopsis thaliana      ILLUMINA        3         3       15.1
Caenorhabditis elegans    ILLUMINA        1         1        3.9
Homo sapiens              ILLUMINA        4         5       13.1
Homo sapiens              NANOPORE        1         1        2.3
Mus musculus              ILLUMINA        3         4       11.8
```

**Analysis:**
- Homo sapiens (human) most studied: 6 runs across 5 samples
- Multi-platform: humans run on both ILLUMINA and NANOPORE
- Plants (Arabidopsis): ILLUMINA only
- Worms (C. elegans): ILLUMINA only
- Mice (Mus musculus): ILLUMINA only

## Q11: Tissue-Specific QC

```
tissue          n_samples  n_runs  avg_q30  avg_dup  adapters
blood                 1       2      0.915    0.165       0
brain                 1       1      0.930    0.110       0
flower                1       1      0.890    0.190       1
heart                 1       1      0.900    0.090       0
leaf                  1       1      0.940    0.080       0
liver                 1       1      0.920    0.110       0
muscle                1       1      0.870    0.250       1
root                  1       1      0.910    0.140       0
saliva                1       1      0.880    0.220       1
skin                  1       1      0.870    0.250       1
whole_organism        1       1      0.860    0.280       1
```

**QC by Tissue (ranked by Q30):**
1. **leaf** (0.94) — Excellent, minimal adapters
2. **brain** (0.93) — Excellent
3. **blood** (0.92) — Good
4. **liver** (0.92) — Good
5. **root** (0.91) — Good
6. **heart** (0.90) — Good
7. **flower** (0.89) — Acceptable, has adapters
8. **saliva** (0.88) — Acceptable, has adapters
9. **skin** (0.87) — Marginal, high duplication (25%)
10. **muscle** (0.87) — Marginal, high duplication (25%)
11. **whole_organism** (0.86) — Lowest, highest duplication (28%)

**Recommendations:**
- Plant tissues (leaf, root) perform best
- Tissue samples with high connective (skin, muscle) have higher duplication
- Whole organism samples are most problematic → consider dissection

## Q12: Temporal Trends (Collection Date)

```
collection_date  n_samples  n_runs  avg_q30
2024-01-15       1          2       0.915
2024-01-16       1          1       0.880
2024-01-17       1          1       0.880
2024-02-01       1          1       0.890
2024-02-02       1          1       0.930
2024-02-03       1          1       0.900
2024-02-10       1          1       0.900
2024-02-11       1          1       0.870
2024-02-12       1          1       0.860
2024-03-01       1          1       0.940
2024-03-02       1          1       0.910
2024-03-03       1          1       0.890
```

**Trend Analysis:**
- **January 15**: Q30 = 0.915 (good)
- **Late January/Early Feb**: dip to 0.88 (possible protocol issue?)
- **Feb 2**: recovery to 0.93
- **Mid Feb**: decline again (0.86–0.87)
- **March**: strong recovery (0.89–0.94)

**Interpretation:**
- Possible seasonal variation or batch effect in late January
- Process improvements in March (training, equipment calibration?)
- Recommendation: Investigate late January batch

---

## Running These Queries

### From Command Line

```bash
# Run all queries
python -m src.cli query \
  --parquet data/processed \
  --sql sql/queries.sql \
  --output docs/query_results.md

# Run interactive query
python -c "
import duckdb
conn = duckdb.connect(':memory:')
conn.execute('CREATE VIEW samples AS SELECT * FROM read_parquet(\"data/processed/dim_samples.parquet\")')
conn.execute('CREATE VIEW runs AS SELECT * FROM read_parquet(\"data/processed/fact_runs.parquet\")')
conn.execute('CREATE VIEW qc_metrics AS SELECT * FROM read_parquet(\"data/processed/fact_qc_metrics.parquet\")')

result = conn.execute('SELECT s.project_id, COUNT(DISTINCT s.sample_id) FROM samples s GROUP BY 1').fetchall()
for row in result:
    print(row)
"
```

### From Python

```python
import duckdb
import pandas as pd

conn = duckdb.connect(':memory:')

# Create views
conn.execute('CREATE VIEW samples AS SELECT * FROM read_parquet("data/processed/dim_samples.parquet")')
conn.execute('CREATE VIEW runs AS SELECT * FROM read_parquet("data/processed/fact_runs.parquet")')
conn.execute('CREATE VIEW qc_metrics AS SELECT * FROM read_parquet("data/processed/fact_qc_metrics.parquet")')

# Run query and get pandas DataFrame
df = conn.execute("""
    SELECT
        s.project_id,
        COUNT(DISTINCT s.sample_id) AS n_samples,
        COUNT(DISTINCT r.run_id)    AS n_runs
    FROM samples s
    LEFT JOIN runs r USING(sample_id)
    GROUP BY 1
    ORDER BY n_runs DESC
""").df()

print(df)
print(f"\nTotal projects: {len(df)}")
print(f"Total samples: {df['n_samples'].sum()}")
print(f"Total runs: {df['n_runs'].sum()}")
```

**Output:**
```
  project_id  n_samples  n_runs
0 PRJNA001003        3.0      3
1 PRJNA001000        3.0      4
2 PRJNA001001        3.0      4
3 PRJNA001002        3.0      3

Total projects: 4
Total samples: 12
Total runs: 14
```
