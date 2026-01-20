"""Pipeline Scheduling Module."""

import schedule
import threading
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional, Dict
import logging

logger = logging.getLogger(__name__)

SCHEDULE_CONFIG = Path("data/.schedule_config.json")


class PipelineScheduler:
    """Scheduler for automated pipeline execution."""
    
    def __init__(self):
        self.jobs = {}
        self.running = False
        self.thread = None
        self.load_schedule()
    
    def add_job(
        self,
        job_name: str,
        func: Callable,
        interval: int,
        unit: str = "hours",  # minutes, hours, days
        params: Optional[Dict] = None
    ):
        """Add a scheduled job."""
        job = schedule.every(interval)
        
        if unit == "minutes":
            job = job.minutes
        elif unit == "hours":
            job = job.hours
        elif unit == "days":
            job = job.days
        
        # Wrap function with params
        if params:
            job.do(func, **params)
        else:
            job.do(func)
        
        self.jobs[job_name] = {
            "job": job,
            "func": func.__name__,
            "interval": interval,
            "unit": unit,
            "params": params or {},
            "created_at": datetime.now().isoformat(),
            "last_run": None
        }
        
        self.save_schedule()
        logger.info(f"Job '{job_name}' scheduled every {interval} {unit}")
    
    def remove_job(self, job_name: str):
        """Remove a scheduled job."""
        if job_name in self.jobs:
            schedule.cancel_job(self.jobs[job_name]["job"])
            del self.jobs[job_name]
            self.save_schedule()
            logger.info(f"Job '{job_name}' removed")
    
    def start(self):
        """Start the scheduler in background thread."""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def _run(self):
        """Internal scheduler loop."""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def get_jobs(self) -> Dict:
        """Get all scheduled jobs."""
        return {
            name: {
                "func": job["func"],
                "interval": job["interval"],
                "unit": job["unit"],
                "created_at": job["created_at"],
                "last_run": job["last_run"]
            }
            for name, job in self.jobs.items()
        }
    
    def save_schedule(self):
        """Save schedule configuration to file."""
        config = {}
        for name, job_info in self.jobs.items():
            config[name] = {
                "func": job_info["func"],
                "interval": job_info["interval"],
                "unit": job_info["unit"],
                "params": job_info["params"]
            }
        
        SCHEDULE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        with open(SCHEDULE_CONFIG, "w") as f:
            json.dump(config, f, indent=2)
    
    def load_schedule(self):
        """Load schedule configuration from file."""
        if not SCHEDULE_CONFIG.exists():
            return
        
        with open(SCHEDULE_CONFIG, "r") as f:
            config = json.load(f)
        
        logger.info(f"Loaded {len(config)} scheduled jobs from config")


# Global scheduler instance
scheduler = PipelineScheduler()


def create_etl_schedule(interval: int, unit: str = "hours", etl_func: Optional[Callable] = None) -> str:
    """Create a scheduled ETL job."""
    if etl_func is None:
        # Default ETL function
        def default_etl():
            from src.etl.ingest import ingest_all
            from src.etl.validate import validate_all
            from src.etl.transform import transform_all
            from src.etl.load import load_to_processed
            from src.history import log_pipeline_run, log_event
            import time
            
            start_time = time.time()
            try:
                dfs = ingest_all(Path("data/raw"))
                is_valid, errors = validate_all(dfs["samples"], dfs["runs"], dfs["qc_metrics"])
                transformed = transform_all(dfs["samples"], dfs["runs"], dfs["qc_metrics"])
                load_to_processed(transformed["samples"], transformed["runs"], transformed["qc_metrics"], Path("data/processed"))
                
                duration = time.time() - start_time
                log_pipeline_run(
                    status="success",
                    samples=len(dfs["samples"]),
                    runs=len(dfs["runs"]),
                    qc=len(dfs["qc_metrics"]),
                    duration=duration,
                    input_dir="data/raw",
                    output_dir="data/processed",
                    mode="strict",
                    errors=errors if not is_valid else None
                )
                logger.info(f"Scheduled ETL completed in {duration:.2f}s")
            except Exception as e:
                logger.error(f"Scheduled ETL failed: {str(e)}")
        
        etl_func = default_etl
    
    job_name = f"etl_schedule_{interval}_{unit}"
    scheduler.add_job(job_name, etl_func, interval, unit)
    return job_name


def list_schedules() -> Dict:
    """List all scheduled jobs."""
    return scheduler.get_jobs()


def cancel_schedule(job_name: str):
    """Cancel a scheduled job."""
    scheduler.remove_job(job_name)


def start_scheduler():
    """Start the global scheduler."""
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler."""
    scheduler.stop()
