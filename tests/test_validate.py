"""Tests for validation module."""

import pytest
import pandas as pd
from src.etl.validate import (
    validate_samples,
    validate_runs,
    validate_qc_metrics,
    validate_foreign_keys,
    ValidationError,
)


class TestValidateSamples:
    """Test validate_samples()"""

    def test_valid_samples(self):
        """Should pass with valid data."""
        df = pd.DataFrame({
            "sample_id": ["S1", "S2", "S3"],
            "project_id": ["P1", "P1", "P2"],
            "organism": ["Homo sapiens", "Homo sapiens", "Mus musculus"],
            "collection_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "tissue": ["blood", "saliva", "liver"],
            "platform": ["ILLUMINA", "NANOPORE", "ILLUMINA"],
        })
        result = validate_samples(df)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_null_sample_id(self):
        """Should fail if sample_id is null."""
        df = pd.DataFrame({
            "sample_id": ["S1", None, "S3"],
            "project_id": ["P1", "P1", "P2"],
            "organism": ["Homo sapiens", "Homo sapiens", "Mus musculus"],
            "collection_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "tissue": ["blood", "saliva", "liver"],
            "platform": ["ILLUMINA", "NANOPORE", "ILLUMINA"],
        })
        result = validate_samples(df)
        assert not result.is_valid
        assert any(e.rule == "NOT_NULL" for e in result.errors)

    def test_duplicate_sample_id(self):
        """Should fail if sample_id is duplicated."""
        df = pd.DataFrame({
            "sample_id": ["S1", "S1", "S3"],
            "project_id": ["P1", "P1", "P2"],
            "organism": ["Homo sapiens", "Homo sapiens", "Mus musculus"],
            "collection_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "tissue": ["blood", "saliva", "liver"],
            "platform": ["ILLUMINA", "NANOPORE", "ILLUMINA"],
        })
        result = validate_samples(df)
        assert not result.is_valid
        assert any(e.rule == "UNIQUE" for e in result.errors)

    def test_invalid_platform(self):
        """Should fail if platform is invalid."""
        df = pd.DataFrame({
            "sample_id": ["S1", "S2"],
            "project_id": ["P1", "P1"],
            "organism": ["Homo sapiens", "Homo sapiens"],
            "collection_date": ["2024-01-01", "2024-01-02"],
            "tissue": ["blood", "saliva"],
            "platform": ["ILLUMINA", "INVALID_PLATFORM"],
        })
        result = validate_samples(df)
        assert not result.is_valid
        assert any(e.rule == "ENUM" for e in result.errors)


class TestValidateRuns:
    """Test validate_runs()"""

    def test_valid_runs(self):
        """Should pass with valid data."""
        df = pd.DataFrame({
            "run_id": ["R1", "R2"],
            "sample_id": ["S1", "S2"],
            "library_layout": ["PAIRED", "SINGLE"],
            "read_length": ["150", "10000"],
            "fastq_gb": ["4.2", "2.1"],
        })
        result = validate_runs(df)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_null_run_id(self):
        """Should fail if run_id is null."""
        df = pd.DataFrame({
            "run_id": ["R1", None],
            "sample_id": ["S1", "S2"],
            "library_layout": ["PAIRED", "SINGLE"],
            "read_length": ["150", "10000"],
            "fastq_gb": ["4.2", "2.1"],
        })
        result = validate_runs(df)
        assert not result.is_valid
        assert any(e.rule == "NOT_NULL" and e.column == "run_id" for e in result.errors)

    def test_invalid_library_layout(self):
        """Should fail if library_layout is invalid."""
        df = pd.DataFrame({
            "run_id": ["R1", "R2"],
            "sample_id": ["S1", "S2"],
            "library_layout": ["PAIRED", "TRIPLET"],
            "read_length": ["150", "10000"],
            "fastq_gb": ["4.2", "2.1"],
        })
        result = validate_runs(df)
        assert not result.is_valid
        assert any(e.rule == "ENUM" for e in result.errors)

    def test_invalid_read_length(self):
        """Should fail if read_length <= 0."""
        df = pd.DataFrame({
            "run_id": ["R1", "R2"],
            "sample_id": ["S1", "S2"],
            "library_layout": ["PAIRED", "SINGLE"],
            "read_length": ["150", "0"],
            "fastq_gb": ["4.2", "2.1"],
        })
        result = validate_runs(df)
        assert not result.is_valid
        assert any(e.rule == "RANGE" and e.column == "read_length" for e in result.errors)

    def test_invalid_fastq_gb(self):
        """Should fail if fastq_gb < 0."""
        df = pd.DataFrame({
            "run_id": ["R1", "R2"],
            "sample_id": ["S1", "S2"],
            "library_layout": ["PAIRED", "SINGLE"],
            "read_length": ["150", "10000"],
            "fastq_gb": ["4.2", "-1.0"],
        })
        result = validate_runs(df)
        assert not result.is_valid
        assert any(e.rule == "RANGE" and e.column == "fastq_gb" for e in result.errors)


class TestValidateQCMetrics:
    """Test validate_qc_metrics()"""

    def test_valid_qc_metrics(self):
        """Should pass with valid data."""
        df = pd.DataFrame({
            "run_id": ["R1", "R2"],
            "total_reads": ["125000000", "130000000"],
            "q30_rate": ["0.92", "0.88"],
            "gc_percent": ["48", "49"],
            "duplication_rate": ["0.15", "0.22"],
            "adapter_content_flag": ["false", "true"],
        })
        result = validate_qc_metrics(df)
        assert result.is_valid

    def test_q30_out_of_range(self):
        """Should fail if q30_rate out of [0, 1]."""
        df = pd.DataFrame({
            "run_id": ["R1", "R2"],
            "total_reads": ["125000000", "130000000"],
            "q30_rate": ["0.92", "1.5"],
            "gc_percent": ["48", "49"],
            "duplication_rate": ["0.15", "0.22"],
            "adapter_content_flag": ["false", "true"],
        })
        result = validate_qc_metrics(df)
        assert not result.is_valid
        assert any(e.rule == "RANGE" and e.column == "q30_rate" for e in result.errors)

    def test_gc_percent_out_of_range(self):
        """Should fail if gc_percent out of [0, 100]."""
        df = pd.DataFrame({
            "run_id": ["R1", "R2"],
            "total_reads": ["125000000", "130000000"],
            "q30_rate": ["0.92", "0.88"],
            "gc_percent": ["48", "105"],
            "duplication_rate": ["0.15", "0.22"],
            "adapter_content_flag": ["false", "true"],
        })
        result = validate_qc_metrics(df)
        assert not result.is_valid
        assert any(e.rule == "RANGE" and e.column == "gc_percent" for e in result.errors)


class TestValidateForeignKeys:
    """Test validate_foreign_keys()"""

    def test_valid_fk(self):
        """Should pass if all sample_ids in runs exist in samples."""
        samples_df = pd.DataFrame({
            "sample_id": ["S1", "S2", "S3"],
        })
        runs_df = pd.DataFrame({
            "run_id": ["R1", "R2"],
            "sample_id": ["S1", "S2"],
        })
        result = validate_foreign_keys(samples_df, runs_df)
        assert result.is_valid

    def test_invalid_fk(self):
        """Should fail if sample_id in runs doesn't exist in samples."""
        samples_df = pd.DataFrame({
            "sample_id": ["S1", "S2"],
        })
        runs_df = pd.DataFrame({
            "run_id": ["R1", "R2"],
            "sample_id": ["S1", "S3"],  # S3 doesn't exist in samples
        })
        result = validate_foreign_keys(samples_df, runs_df)
        assert not result.is_valid
        assert any(e.rule == "FK_CHECK" for e in result.errors)
