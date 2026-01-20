"""Quality Metrics Dashboard Module - Genomics-specific QC analysis."""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def analyze_qc_metrics(qc_df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze QC metrics with genomics-specific insights."""
    
    analysis = {
        "q30_stats": {},
        "gc_stats": {},
        "duplication_stats": {},
        "adapter_stats": {},
        "summary": {}
    }
    
    # Q30 Analysis (Quality Score)
    if "q30_rate" in qc_df.columns:
        q30 = qc_df["q30_rate"]
        analysis["q30_stats"] = {
            "min": float(q30.min()),
            "max": float(q30.max()),
            "mean": float(q30.mean()),
            "median": float(q30.median()),
            "std": float(q30.std()),
            "samples_below_90": int((q30 < 90).sum()),
            "samples_below_80": int((q30 < 80).sum()),
            "pass_rate": float((q30 >= 90).sum() / len(q30) * 100)  # Q30 >= 90% is good
        }
    
    # GC% Analysis
    if "gc_percent" in qc_df.columns:
        gc = qc_df["gc_percent"]
        analysis["gc_stats"] = {
            "min": float(gc.min()),
            "max": float(gc.max()),
            "mean": float(gc.mean()),
            "median": float(gc.median()),
            "std": float(gc.std()),
            "optimal_range": (40, 60),
            "samples_in_range": int(((gc >= 40) & (gc <= 60)).sum()),
            "range_percentage": float(((gc >= 40) & (gc <= 60)).sum() / len(gc) * 100)
        }
    
    # Duplication Analysis
    if "duplication_rate" in qc_df.columns:
        dup = qc_df["duplication_rate"]
        analysis["duplication_stats"] = {
            "min": float(dup.min()),
            "max": float(dup.max()),
            "mean": float(dup.mean()),
            "median": float(dup.median()),
            "samples_above_10": int((dup > 10).sum()),  # >10% duplication is high
            "high_dup_rate": float((dup > 10).sum() / len(dup) * 100)
        }
    
    # Adapter Analysis
    if "adapter_content_flag" in qc_df.columns:
        adapter = qc_df["adapter_content_flag"]
        adapter_count = (adapter == True).sum() if adapter.dtype == bool else (adapter == 1).sum()
        analysis["adapter_stats"] = {
            "flagged_samples": int(adapter_count),
            "flag_percentage": float(adapter_count / len(adapter) * 100)
        }
    
    # Overall Quality Score (0-100)
    quality_score = 100
    if "q30_rate" in qc_df.columns:
        q30_pass = (qc_df["q30_rate"] >= 90).sum() / len(qc_df) * 100
        quality_score -= max(0, (100 - q30_pass) * 0.5)
    
    if "gc_percent" in qc_df.columns:
        gc_pass = ((qc_df["gc_percent"] >= 40) & (qc_df["gc_percent"] <= 60)).sum() / len(qc_df) * 100
        quality_score -= max(0, (100 - gc_pass) * 0.3)
    
    if "duplication_rate" in qc_df.columns:
        dup_pass = (qc_df["duplication_rate"] <= 10).sum() / len(qc_df) * 100
        quality_score -= max(0, (100 - dup_pass) * 0.2)
    
    analysis["summary"]["overall_quality_score"] = max(0, min(100, quality_score))
    analysis["summary"]["samples_count"] = len(qc_df)
    
    return analysis


def get_qc_thresholds() -> Dict[str, Dict[str, Any]]:
    """Get recommended QC thresholds for genomics data."""
    return {
        "q30_rate": {
            "unit": "%",
            "description": "Percentage of bases with quality score >= 30",
            "good": {"min": 90, "max": 100},
            "acceptable": {"min": 80, "max": 90},
            "poor": {"max": 80}
        },
        "gc_percent": {
            "unit": "%",
            "description": "GC content percentage",
            "good": {"min": 40, "max": 60},
            "acceptable": {"min": 35, "max": 65},
            "poor": {"outside": (35, 65)}
        },
        "duplication_rate": {
            "unit": "%",
            "description": "Percentage of duplicate reads",
            "good": {"max": 5},
            "acceptable": {"max": 10},
            "poor": {"min": 10}
        },
        "adapter_content": {
            "unit": "flag",
            "description": "Presence of adapter sequences",
            "good": 0,
            "poor": 1
        }
    }


def flag_outliers(qc_df: pd.DataFrame, field: str, threshold_type: str = "iqr") -> List[int]:
    """Flag outlier samples in QC metrics."""
    
    if field not in qc_df.columns:
        return []
    
    data = qc_df[field].dropna()
    
    if threshold_type == "iqr":
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        outliers = data[(data < Q1 - 1.5 * IQR) | (data > Q3 + 1.5 * IQR)].index.tolist()
    else:  # z-score
        z_scores = np.abs((data - data.mean()) / data.std())
        outliers = data[z_scores > 3].index.tolist()
    
    return outliers


def get_failed_samples(qc_df: pd.DataFrame, samples_df: pd.DataFrame = None) -> Dict[str, Any]:
    """Get samples that failed QC thresholds."""
    
    failed = {
        "by_q30": [],
        "by_gc": [],
        "by_duplication": [],
        "by_adapter": [],
        "total_failed": []
    }
    
    # Q30 failures
    if "q30_rate" in qc_df.columns:
        failed["by_q30"] = qc_df[qc_df["q30_rate"] < 80]["run_id"].tolist()
    
    # GC failures
    if "gc_percent" in qc_df.columns:
        gc = qc_df["gc_percent"]
        failed["by_gc"] = qc_df[(gc < 35) | (gc > 65)]["run_id"].tolist()
    
    # Duplication failures
    if "duplication_rate" in qc_df.columns:
        failed["by_duplication"] = qc_df[qc_df["duplication_rate"] > 15]["run_id"].tolist()
    
    # Adapter failures
    if "adapter_content_flag" in qc_df.columns:
        failed["by_adapter"] = qc_df[qc_df["adapter_content_flag"] == 1]["run_id"].tolist()
    
    # Total failed
    failed_samples = set(
        failed["by_q30"] + failed["by_gc"] + 
        failed["by_duplication"] + failed["by_adapter"]
    )
    failed["total_failed"] = list(failed_samples)
    
    return failed


def generate_qc_report(qc_df: pd.DataFrame) -> str:
    """Generate text QC report."""
    
    analysis = analyze_qc_metrics(qc_df)
    thresholds = get_qc_thresholds()
    
    report = f"""
╔════════════════════════════════════════════════════╗
║         🧬 QUALITY CONTROL REPORT                  ║
╚════════════════════════════════════════════════════╝

📊 OVERALL QUALITY SCORE: {analysis['summary']['overall_quality_score']:.1f}/100

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 Q30 RATE (Base Quality)
   Mean: {analysis['q30_stats'].get('mean', 'N/A')}%
   Pass Rate: {analysis['q30_stats'].get('pass_rate', 'N/A'):.1f}%
   Failed (< 80%): {analysis['q30_stats'].get('samples_below_80', 0)}

📏 GC CONTENT (%)
   Mean: {analysis['gc_stats'].get('mean', 'N/A'):.1f}%
   Optimal Range (40-60%): {analysis['gc_stats'].get('range_percentage', 'N/A'):.1f}%

🔄 DUPLICATION RATE (%)
   Mean: {analysis['duplication_stats'].get('mean', 'N/A'):.1f}%
   High (> 10%): {analysis['duplication_stats'].get('high_dup_rate', 'N/A'):.1f}%

📎 ADAPTER CONTENT
   Flagged: {analysis['adapter_stats'].get('flagged_samples', 0)} samples

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ RECOMMENDATIONS:
   1. Review samples with Q30 < 80%
   2. Check GC content outside 40-60% range
   3. Investigate high duplication rates (> 10%)
   4. Address adapter sequences if flagged

Report Generated: {pd.Timestamp.now().isoformat()}
"""
    
    return report
