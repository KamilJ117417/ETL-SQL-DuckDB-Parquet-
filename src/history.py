"""Pipeline History and Audit Log Module."""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

HISTORY_DB = Path("data/.pipeline_history.db")


def init_history_db():
    """Initialize SQLite database for pipeline history."""
    HISTORY_DB.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            samples_processed INTEGER,
            runs_processed INTEGER,
            qc_processed INTEGER,
            duration_seconds REAL,
            input_dir TEXT,
            output_dir TEXT,
            mode TEXT,
            errors TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            message TEXT,
            timestamp TEXT,
            FOREIGN KEY (pipeline_id) REFERENCES pipeline_runs(id)
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info(f"History DB initialized at {HISTORY_DB}")


def log_pipeline_run(
    status: str,
    samples: int,
    runs: int,
    qc: int,
    duration: float,
    input_dir: str,
    output_dir: str,
    mode: str,
    errors: Optional[List[str]] = None
) -> int:
    """Log a pipeline run to history."""
    init_history_db()
    
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    errors_json = json.dumps(errors or [])
    
    cursor.execute("""
        INSERT INTO pipeline_runs 
        (timestamp, status, samples_processed, runs_processed, qc_processed, 
         duration_seconds, input_dir, output_dir, mode, errors)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, status, samples, runs, qc, duration, input_dir, output_dir, mode, errors_json))
    
    pipeline_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    logger.info(f"Pipeline run logged with ID {pipeline_id}")
    return pipeline_id


def log_event(pipeline_id: int, event_type: str, message: str):
    """Log an event for a pipeline run."""
    init_history_db()
    
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO pipeline_events (pipeline_id, event_type, message, timestamp)
        VALUES (?, ?, ?, ?)
    """, (pipeline_id, event_type, message, timestamp))
    
    conn.commit()
    conn.close()


def get_pipeline_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Get pipeline run history."""
    init_history_db()
    
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, timestamp, status, samples_processed, runs_processed, 
               qc_processed, duration_seconds, mode
        FROM pipeline_runs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            "id": row[0],
            "timestamp": row[1],
            "status": row[2],
            "samples": row[3],
            "runs": row[4],
            "qc": row[5],
            "duration": row[6],
            "mode": row[7]
        })
    
    return history


def get_pipeline_stats() -> Dict[str, Any]:
    """Get overall pipeline statistics."""
    init_history_db()
    
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM pipeline_runs")
    total_runs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM pipeline_runs WHERE status = 'success'")
    successful_runs = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(duration_seconds) FROM pipeline_runs")
    total_duration = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(samples_processed) FROM pipeline_runs WHERE status = 'success'")
    total_samples = cursor.fetchone()[0] or 0
    
    conn.close()
    
    success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
    
    return {
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "failed_runs": total_runs - successful_runs,
        "success_rate": success_rate,
        "total_duration_seconds": total_duration,
        "total_samples_processed": total_samples,
        "avg_duration_seconds": total_duration / total_runs if total_runs > 0 else 0
    }


def get_events_for_run(pipeline_id: int) -> List[Dict[str, Any]]:
    """Get all events for a specific pipeline run."""
    init_history_db()
    
    conn = sqlite3.connect(HISTORY_DB)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT event_type, message, timestamp
        FROM pipeline_events
        WHERE pipeline_id = ?
        ORDER BY timestamp ASC
    """, (pipeline_id,))
    
    events = []
    for row in cursor.fetchall():
        events.append({
            "type": row[0],
            "message": row[1],
            "timestamp": row[2]
        })
    
    conn.close()
    return events


def clear_history():
    """Clear all pipeline history."""
    if HISTORY_DB.exists():
        HISTORY_DB.unlink()
        logger.info("Pipeline history cleared")


def export_history(output_path: Path = Path("docs/pipeline_history.json")):
    """Export history to JSON file."""
    init_history_db()
    
    history = get_pipeline_history(limit=1000)
    stats = get_pipeline_stats()
    
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "statistics": stats,
        "runs": history
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(export_data, f, indent=2)
    
    logger.info(f"History exported to {output_path}")
    return str(output_path)
