"""Report Generation Module - Generate HTML/Markdown reports."""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def generate_html_report(
    pipeline_results: Dict[str, Any],
    profile_results: Dict[str, Any],
    output_path: Path = Path("docs/report.html")
) -> str:
    """Generate comprehensive HTML report."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🧬 Genomics ETL Report</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            .header h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
            }}
            .timestamp {{
                font-size: 0.9em;
                opacity: 0.9;
            }}
            .content {{
                padding: 40px;
            }}
            .section {{
                margin-bottom: 40px;
            }}
            .section h2 {{
                color: #667eea;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
                margin-bottom: 20px;
                font-size: 1.8em;
            }}
            .metrics {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .metric {{
                background: #f0f2f6;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                border-left: 4px solid #667eea;
            }}
            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
                margin: 10px 0;
            }}
            .metric-label {{
                color: #666;
                font-size: 0.9em;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th {{
                background: #667eea;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: bold;
            }}
            td {{
                padding: 12px;
                border-bottom: 1px solid #ddd;
            }}
            tr:hover {{
                background: #f5f5f5;
            }}
            .success {{
                background: #d4edda;
                border-left-color: #28a745;
            }}
            .warning {{
                background: #fff3cd;
                border-left-color: #ffc107;
            }}
            .error {{
                background: #f8d7da;
                border-left-color: #dc3545;
            }}
            .quality-score {{
                font-size: 3em;
                font-weight: bold;
                text-align: center;
            }}
            .quality-score.high {{ color: #28a745; }}
            .quality-score.medium {{ color: #ffc107; }}
            .quality-score.low {{ color: #dc3545; }}
            .footer {{
                background: #f0f2f6;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 0.9em;
                border-top: 1px solid #ddd;
            }}
            .progress-bar {{
                width: 100%;
                height: 20px;
                background: #e0e0e0;
                border-radius: 10px;
                overflow: hidden;
                margin: 10px 0;
            }}
            .progress-fill {{
                height: 100%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                width: var(--width);
                transition: width 0.3s ease;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🧬 Genomics ETL Pipeline Report</h1>
                <p class="timestamp">Generated: {timestamp}</p>
            </div>
            
            <div class="content">
                <!-- Pipeline Summary -->
                <div class="section">
                    <h2>📊 Pipeline Summary</h2>
                    <div class="metrics">
                        <div class="metric success">
                            <div class="metric-label">Samples Processed</div>
                            <div class="metric-value">{pipeline_results.get("samples", 0)}</div>
                        </div>
                        <div class="metric success">
                            <div class="metric-label">Runs Processed</div>
                            <div class="metric-value">{pipeline_results.get("runs", 0)}</div>
                        </div>
                        <div class="metric success">
                            <div class="metric-label">QC Metrics</div>
                            <div class="metric-value">{pipeline_results.get("qc_metrics", 0)}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Status</div>
                            <div class="metric-value">✅</div>
                        </div>
                    </div>
                </div>
                
                <!-- Data Quality -->
                <div class="section">
                    <h2>📈 Data Quality Analysis</h2>
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-label">Quality Score</div>
                            <div class="metric-value">{profile_results.get("quality_score", 0):.1f}%</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Missing Cells</div>
                            <div class="metric-value">{profile_results.get("missing_cells", 0)}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Duplicate Rows</div>
                            <div class="metric-value">{profile_results.get("duplicate_rows", 0)}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Total Cells</div>
                            <div class="metric-value">{profile_results.get("total_cells", 0)}</div>
                        </div>
                    </div>
                </div>
                
                <!-- Column Analysis -->
                <div class="section">
                    <h2>🔍 Column Analysis</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Column</th>
                                <th>Completeness</th>
                                <th>Missing</th>
                                <th>Unique Values</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    # Add column quality rows
    for col, quality in profile_results.get("column_quality", {}).items():
        completeness = quality.get("completeness", 0)
        bar_width = completeness
        html_content += f"""
                            <tr>
                                <td>{col}</td>
                                <td>
                                    <div class="progress-bar">
                                        <div class="progress-fill" style="--width: {bar_width}%"></div>
                                    </div>
                                    {completeness:.1f}%
                                </td>
                                <td>{quality.get("missing", 0)}</td>
                                <td>{quality.get("unique", 0)}</td>
                            </tr>
        """
    
    html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="footer">
                <p>🧬 Genomics ETL Pipeline | Report v1.0</p>
                <p>© 2026 | All rights reserved</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html_content)
    
    logger.info(f"HTML report saved to {output_path}")
    return str(output_path)


def generate_markdown_report(
    pipeline_results: Dict[str, Any],
    profile_results: Dict[str, Any],
    output_path: Path = Path("docs/report.md")
) -> str:
    """Generate comprehensive Markdown report."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md_content = f"""# 🧬 Genomics ETL Pipeline Report

**Generated**: {timestamp}

---

## 📊 Executive Summary

### Pipeline Results
- **Samples Processed**: {pipeline_results.get("samples", 0)}
- **Runs Processed**: {pipeline_results.get("runs", 0)}
- **QC Metrics**: {pipeline_results.get("qc_metrics", 0)}
- **Status**: ✅ SUCCESS

---

## 📈 Data Quality Metrics

### Overall Quality
- **Quality Score**: {profile_results.get("quality_score", 0):.1f}%
- **Total Rows**: {profile_results.get("total_rows", 0)}
- **Total Columns**: {profile_results.get("total_columns", 0)}
- **Missing Cells**: {profile_results.get("missing_cells", 0)}
- **Duplicate Rows**: {profile_results.get("duplicate_rows", 0)}
- **Completeness**: {100 - (profile_results.get("missing_cells", 0) / profile_results.get("total_cells", 1) * 100):.2f}%

### Column Quality Summary

| Column | Completeness | Missing | Unique |
|--------|--------------|---------|--------|
"""
    
    for col, quality in profile_results.get("column_quality", {}).items():
        completeness = quality.get("completeness", 0)
        missing = quality.get("missing", 0)
        unique = quality.get("unique", 0)
        md_content += f"| {col} | {completeness:.1f}% | {missing} | {unique} |\n"
    
    md_content += """

---

## ✅ Recommendations

1. **Data Quality**: Monitor columns with <95% completeness
2. **Duplicates**: Review and handle duplicate rows
3. **Outliers**: Investigate unusual values in numeric columns
4. **Schema**: Validate data types and constraints

---

**Report Version**: 1.0  
**Status**: ✅ Complete
"""
    
    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(md_content)
    
    logger.info(f"Markdown report saved to {output_path}")
    return str(output_path)
