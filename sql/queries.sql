-- DuckDB SQL queries for genomics metadata analysis

-- Q1: Samples and runs per project
SELECT
  s.project_id,
  COUNT(DISTINCT s.sample_id) AS n_samples,
  COUNT(DISTINCT r.run_id)    AS n_runs,
  ROUND(SUM(r.fastq_gb), 2)   AS total_fastq_gb
FROM samples s
LEFT JOIN runs r USING(sample_id)
GROUP BY 1
ORDER BY n_runs DESC;

-- Q2: Top 10 runs with worst Q30 (lowest quality)
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

-- Q3: Quality control status flags (problematic runs)
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

-- Q4: Average QC metrics by platform
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

-- Q5: Total FASTQ storage per project (cost/storage analysis)
SELECT
  r.project_id,
  COUNT(DISTINCT r.run_id) AS n_runs,
  ROUND(SUM(r.fastq_gb), 2) AS total_fastq_gb,
  ROUND(AVG(r.fastq_gb), 2) AS avg_fastq_gb_per_run
FROM runs r
GROUP BY 1
ORDER BY total_fastq_gb DESC;

-- Q6: Window function - Ranking runs by Q30 within each project (worst to best)
SELECT
  r.project_id,
  q.run_id,
  q.q30_rate,
  RANK() OVER (PARTITION BY r.project_id ORDER BY q.q30_rate ASC) AS rank_worst_q30,
  ROW_NUMBER() OVER (PARTITION BY r.project_id ORDER BY q.q30_rate DESC) AS rank_best_q30
FROM qc_metrics q
JOIN runs r USING(run_id)
ORDER BY r.project_id, rank_worst_q30;

-- Q7: Data completeness - Null rates in critical fields
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

-- Q8: Referential integrity check - Runs without corresponding samples
SELECT r.run_id, r.sample_id
FROM runs r
LEFT JOIN samples s USING(sample_id)
WHERE s.sample_id IS NULL
ORDER BY r.run_id;

-- Q9: Library layout distribution across projects
SELECT
  s.project_id,
  r.library_layout,
  COUNT(DISTINCT r.run_id) AS n_runs,
  ROUND(100.0 * COUNT(DISTINCT r.run_id) / SUM(COUNT(DISTINCT r.run_id)) OVER (PARTITION BY s.project_id), 1) AS percent
FROM runs r
JOIN samples s USING(sample_id)
GROUP BY 1, 2
ORDER BY s.project_id, n_runs DESC;

-- Q10: Platform distribution by organism
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

-- Q11: Tissue-specific quality metrics
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

-- Q12: Collection date analysis (temporal trends)
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
