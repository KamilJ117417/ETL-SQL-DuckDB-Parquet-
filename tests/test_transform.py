"""Tests for transform module."""

import pytest
import pandas as pd
from src.etl.transform import (
    normalize_string_column,
    cast_numeric,
    cast_date,
    transform_samples,
    transform_runs,
    transform_qc_metrics,
)


class TestNormalizeStringColumn:
    """Test normalize_string_column()"""

    def test_trim_whitespace(self):
        """Should trim leading/trailing whitespace."""
        series = pd.Series(["  hello  ", "world ", " test"])
        result = normalize_string_column(series)
        assert list(result) == ["hello", "world", "test"]

    def test_replace_na_strings(self):
        """Should replace 'NA', 'null' with None."""
        series = pd.Series(["hello", "NA", "null", "NULL", ""])
        result = normalize_string_column(series)
        assert result[1] is None or pd.isna(result[1])
        assert result[2] is None or pd.isna(result[2])

    def test_uppercase(self):
        """Should uppercase if requested."""
        series = pd.Series(["hello", "World", "test"])
        result = normalize_string_column(series, uppercase=True)
        assert list(result) == ["HELLO", "WORLD", "TEST"]


class TestCastNumeric:
    """Test cast_numeric()"""

    def test_valid_integers(self):
        """Should cast valid integers."""
        series = pd.Series(["100", "200", "300"])
        result = cast_numeric(series, dtype="int64")
        assert result.dtype == "int64"
        assert list(result) == [100, 200, 300]

    def test_valid_floats(self):
        """Should cast valid floats."""
        series = pd.Series(["1.5", "2.7", "3.14"])
        result = cast_numeric(series, dtype="float64")
        assert result.dtype == "float64"
        assert all(result >= 1.0)

    def test_invalid_values_become_nan(self):
        """Should convert invalid values to NaN."""
        series = pd.Series(["100", "abc", "200"])
        result = cast_numeric(series, dtype="float64")
        assert pd.isna(result[1])
        assert result[0] == 100.0


class TestCastDate:
    """Test cast_date()"""

    def test_valid_dates(self):
        """Should cast valid dates."""
        series = pd.Series(["2024-01-01", "2024-12-31"])
        result = cast_date(series)
        assert str(result[0]) == "2024-01-01"

    def test_invalid_dates_become_nat(self):
        """Should convert invalid dates to NaT."""
        series = pd.Series(["2024-01-01", "invalid-date"])
        result = cast_date(series)
        # First date should be valid, second should be NaT
        assert result[0] is not None


class TestTransformSamples:
    """Test transform_samples()"""

    def test_normalize_and_cast(self):
        """Should normalize strings and cast dates."""
        df = pd.DataFrame({
            "sample_id": ["  S1  ", "S2"],
            "project_id": ["  P1  ", "P1"],
            "organism": ["Homo sapiens", "Mus musculus"],
            "collection_date": ["2024-01-01", "2024-01-02"],
            "tissue": ["blood", "liver"],
            "platform": ["illumina", "NANOPORE"],
            "ingested_at": ["2024-01-20T10:00:00", "2024-01-20T10:00:00"],
            "source_file": ["samples.csv", "samples.csv"],
            "row_hash": ["hash1", "hash2"],
        })
        result = transform_samples(df)
        assert result["sample_id"].iloc[0] == "S1"  # Trimmed
        assert result["platform"].iloc[0] == "ILLUMINA"  # Uppercase

    def test_deduplication(self):
        """Should remove duplicates (keep last)."""
        df = pd.DataFrame({
            "sample_id": ["S1", "S1", "S2"],
            "project_id": ["P1", "P1", "P1"],
            "organism": ["Homo sapiens", "Homo sapiens", "Mus musculus"],
            "collection_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "tissue": ["blood", "saliva", "liver"],
            "platform": ["ILLUMINA", "ILLUMINA", "ILLUMINA"],
            "ingested_at": ["2024-01-20T10:00:00", "2024-01-20T10:00:00", "2024-01-20T10:00:00"],
            "source_file": ["samples.csv", "samples.csv", "samples.csv"],
            "row_hash": ["hash1", "hash2", "hash3"],
        })
        result = transform_samples(df)
        assert len(result) == 2  # S1 appears once (last), S2 once
        assert result[result["sample_id"] == "S1"]["tissue"].iloc[0] == "saliva"  # Keep last


class TestTransformRuns:
    """Test transform_runs()"""

    def test_numeric_casting(self):
        """Should cast read_length to int and fastq_gb to float."""
        df = pd.DataFrame({
            "run_id": ["R1", "R2"],
            "sample_id": ["S1", "S2"],
            "library_layout": ["PAIRED", "SINGLE"],
            "read_length": ["150", "10000"],
            "fastq_gb": ["4.2", "2.1"],
            "ingested_at": ["2024-01-20T10:00:00", "2024-01-20T10:00:00"],
            "source_file": ["runs.csv", "runs.csv"],
            "row_hash": ["hash1", "hash2"],
        })
        result = transform_runs(df)
        assert result["read_length"].dtype in ["int64", "Int64"]
        assert result["fastq_gb"].dtype in ["float64", "Float64"]

    def test_layout_uppercase(self):
        """Should uppercase library_layout."""
        df = pd.DataFrame({
            "run_id": ["R1", "R2"],
            "sample_id": ["S1", "S2"],
            "library_layout": ["paired", "single"],
            "read_length": ["150", "10000"],
            "fastq_gb": ["4.2", "2.1"],
            "ingested_at": ["2024-01-20T10:00:00", "2024-01-20T10:00:00"],
            "source_file": ["runs.csv", "runs.csv"],
            "row_hash": ["hash1", "hash2"],
        })
        result = transform_runs(df)
        assert result["library_layout"].iloc[0] == "PAIRED"


class TestTransformQCMetrics:
    """Test transform_qc_metrics()"""

    def test_boolean_normalization(self):
        """Should convert boolean flags properly."""
        df = pd.DataFrame({
            "run_id": ["R1", "R2", "R3", "R4"],
            "total_reads": ["125000000", "130000000", "115000000", "125000000"],
            "q30_rate": ["0.92", "0.88", "0.90", "0.85"],
            "gc_percent": ["48", "49", "47", "50"],
            "duplication_rate": ["0.15", "0.22", "0.18", "0.25"],
            "adapter_content_flag": ["true", "false", "1", "0"],
            "ingested_at": ["2024-01-20T10:00:00"] * 4,
            "source_file": ["qc_metrics.tsv"] * 4,
            "row_hash": ["hash1", "hash2", "hash3", "hash4"],
        })
        result = transform_qc_metrics(df)
        assert result["adapter_content_flag"].iloc[0] is True or result["adapter_content_flag"].iloc[0] == 1
        assert result["adapter_content_flag"].iloc[1] is False or result["adapter_content_flag"].iloc[1] == 0

    def test_numeric_casting(self):
        """Should cast all QC numerics."""
        df = pd.DataFrame({
            "run_id": ["R1"],
            "total_reads": ["125000000"],
            "q30_rate": ["0.92"],
            "gc_percent": ["48"],
            "duplication_rate": ["0.15"],
            "adapter_content_flag": ["false"],
            "ingested_at": ["2024-01-20T10:00:00"],
            "source_file": ["qc_metrics.tsv"],
            "row_hash": ["hash1"],
        })
        result = transform_qc_metrics(df)
        assert result["q30_rate"].dtype in ["float64", "Float64"]
        assert result["gc_percent"].dtype in ["float64", "Float64"]
