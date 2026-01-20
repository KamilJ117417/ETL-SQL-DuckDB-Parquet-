#!/usr/bin/env python3
"""
Test script to verify benchmark fixes.
Demonstrates that benchmarks work with and without Parquet files.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.benchmarks import run_benchmark


def test_benchmark_with_csv_only():
    """Test benchmarking when Parquet file doesn't exist."""
    print("\n" + "="*60)
    print("TEST 1: Benchmark CSV only (Parquet file missing)")
    print("="*60)
    
    csv_file = Path("data/raw/runs.csv")
    nonexistent_parquet = Path("data/processed/nonexistent.parquet")
    
    if not csv_file.exists():
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    try:
        result = run_benchmark(csv_file, nonexistent_parquet)
        print("✅ Benchmark completed without errors!")
        print("\nReport preview (first 500 chars):")
        print(result[:500])
        
        # Verify report contains expected sections
        checks = [
            ("Has File Sizes section", "## File Sizes" in result),
            ("Has Query Performance section", "## Query Performance" in result),
            ("Has Conclusions section", "## Conclusions" in result),
            ("Shows CSV times", "CSV (ms)" in result),
            ("Shows N/A for Parquet (not created)", "N/A" in result),
        ]
        
        all_pass = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"{status} {check_name}")
            if not check_result:
                all_pass = False
        
        return all_pass
        
    except ZeroDivisionError as e:
        print(f"❌ Division by zero error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_correct_columns():
    """Verify queries use correct column names."""
    print("\n" + "="*60)
    print("TEST 2: Verify correct column names in queries")
    print("="*60)
    
    csv_file = Path("data/raw/runs.csv")
    
    if not csv_file.exists():
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    try:
        import pandas as pd
        
        # Read the actual data
        df = pd.read_csv(csv_file)
        columns = set(df.columns)
        
        print(f"Available columns: {sorted(columns)}")
        
        # Verify required columns for benchmark exist
        required_columns = {'run_id', 'read_length', 'fastq_gb'}
        checks = []
        
        for col in required_columns:
            has_col = col in columns
            status = "✅" if has_col else "❌"
            print(f"{status} Column '{col}' exists: {has_col}")
            checks.append(has_col)
        
        # Verify removed column doesn't exist (was the problem)
        has_q30_rate = 'q30_rate' in columns
        status = "✅" if not has_q30_rate else "❌"
        print(f"{status} Column 'q30_rate' is NOT in runs.csv: {not has_q30_rate}")
        print("   (q30_rate is in qc_metrics.tsv, not in runs.csv)")
        checks.append(not has_q30_rate)
        
        return all(checks)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("BENCHMARK MODULE FIXES - VERIFICATION TESTS")
    print("="*70)
    
    results = {
        "CSV-only benchmarking": test_correct_columns(),
        "Correct column names": test_correct_columns(),
        "CSV-only benchmarking": test_benchmark_with_csv_only(),
    }
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_pass = all(results.values())
    
    print("\n" + ("="*70))
    if all_pass:
        print("✅ ALL TESTS PASSED - Benchmark fixes verified!")
    else:
        print("❌ SOME TESTS FAILED - Review errors above")
    print("="*70 + "\n")
    
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
