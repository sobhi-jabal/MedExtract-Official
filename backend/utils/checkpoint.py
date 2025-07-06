"""
Checkpoint management utilities for job persistence and recovery
Based on robust job management patterns from provided examples
"""

import json
import os
import pickle
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.jobs import ExtractionJob, JobStatus


class CheckpointManager:
    """
    Manages job checkpoints for recovery and persistence
    Handles both metadata and data checkpointing
    """
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.checkpoint_dir / "jobs").mkdir(exist_ok=True)
        (self.checkpoint_dir / "data").mkdir(exist_ok=True)
        (self.checkpoint_dir / "results").mkdir(exist_ok=True)
        
    def save_job_checkpoint(self, job: ExtractionJob) -> bool:
        """Save job metadata checkpoint"""
        try:
            checkpoint_path = self.checkpoint_dir / "jobs" / f"{job.job_id}.json"
            
            # Convert job to dictionary for serialization
            job_dict = {
                "job_id": job.job_id,
                "name": job.name,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "total_rows": job.total_rows,
                "processed_rows": job.processed_rows,
                "successful_rows": job.successful_rows,
                "failed_rows": job.failed_rows,
                "progress_percentage": job.progress_percentage,
                "current_step": job.current_step,
                "total_steps": job.total_steps,
                "error_message": job.error_message,
                "config_snapshot": job.config_snapshot,
                "intermediate_results": job.intermediate_results,
                "processing_stats": job.processing_stats
            }
            
            with open(checkpoint_path, 'w') as f:
                json.dump(job_dict, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving job checkpoint {job.job_id}: {e}")
            return False
    
    def load_job_checkpoint(self, job_id: str) -> Optional[ExtractionJob]:
        """Load job from checkpoint"""
        try:
            checkpoint_path = self.checkpoint_dir / "jobs" / f"{job_id}.json"
            
            if not checkpoint_path.exists():
                return None
            
            with open(checkpoint_path, 'r') as f:
                job_dict = json.load(f)
            
            # Reconstruct job object
            job = ExtractionJob(
                job_id=job_dict["job_id"],
                name=job_dict["name"]
            )
            
            # Restore state
            job.status = JobStatus(job_dict["status"])
            job.created_at = datetime.fromisoformat(job_dict["created_at"])
            job.updated_at = datetime.fromisoformat(job_dict["updated_at"])
            job.started_at = datetime.fromisoformat(job_dict["started_at"]) if job_dict["started_at"] else None
            job.completed_at = datetime.fromisoformat(job_dict["completed_at"]) if job_dict["completed_at"] else None
            job.total_rows = job_dict["total_rows"]
            job.processed_rows = job_dict["processed_rows"]
            job.successful_rows = job_dict["successful_rows"]
            job.failed_rows = job_dict["failed_rows"]
            job.progress_percentage = job_dict["progress_percentage"]
            job.current_step = job_dict["current_step"]
            job.total_steps = job_dict["total_steps"]
            job.error_message = job_dict["error_message"]
            job.config_snapshot = job_dict["config_snapshot"]
            job.intermediate_results = job_dict["intermediate_results"]
            job.processing_stats = job_dict["processing_stats"]
            
            return job
            
        except Exception as e:
            print(f"Error loading job checkpoint {job_id}: {e}")
            return None
    
    def save_data_checkpoint(
        self, 
        job_id: str, 
        df: pd.DataFrame, 
        step: str = "processed"
    ) -> bool:
        """Save DataFrame checkpoint"""
        try:
            data_path = self.checkpoint_dir / "data" / f"{job_id}_{step}.pkl"
            
            with open(data_path, 'wb') as f:
                pickle.dump(df, f)
            
            return True
            
        except Exception as e:
            print(f"Error saving data checkpoint {job_id}_{step}: {e}")
            return False
    
    def load_data_checkpoint(self, job_id: str, step: str = "processed") -> Optional[pd.DataFrame]:
        """Load DataFrame from checkpoint"""
        try:
            data_path = self.checkpoint_dir / "data" / f"{job_id}_{step}.pkl"
            
            if not data_path.exists():
                return None
            
            with open(data_path, 'rb') as f:
                return pickle.load(f)
                
        except Exception as e:
            print(f"Error loading data checkpoint {job_id}_{step}: {e}")
            return None
    
    def save_results_checkpoint(
        self, 
        job_id: str, 
        results: Dict[str, Any]
    ) -> bool:
        """Save final results checkpoint"""
        try:
            results_path = self.checkpoint_dir / "results" / f"{job_id}_results.json"
            
            # Make results JSON serializable
            serializable_results = self._make_serializable(results)
            
            with open(results_path, 'w') as f:
                json.dump(serializable_results, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving results checkpoint {job_id}: {e}")
            return False
    
    def load_results_checkpoint(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Load results from checkpoint"""
        try:
            results_path = self.checkpoint_dir / "results" / f"{job_id}_results.json"
            
            if not results_path.exists():
                return None
            
            with open(results_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error loading results checkpoint {job_id}: {e}")
            return None
    
    def list_job_checkpoints(self) -> List[str]:
        """List all available job checkpoints"""
        try:
            jobs_dir = self.checkpoint_dir / "jobs"
            if not jobs_dir.exists():
                return []
            
            job_files = [f.stem for f in jobs_dir.glob("*.json")]
            return sorted(job_files)
            
        except Exception as e:
            print(f"Error listing job checkpoints: {e}")
            return []
    
    def delete_job_checkpoint(self, job_id: str) -> bool:
        """Delete all checkpoints for a job"""
        try:
            # Delete job metadata
            job_path = self.checkpoint_dir / "jobs" / f"{job_id}.json"
            if job_path.exists():
                job_path.unlink()
            
            # Delete data checkpoints
            data_dir = self.checkpoint_dir / "data"
            for data_file in data_dir.glob(f"{job_id}_*.pkl"):
                data_file.unlink()
            
            # Delete results
            results_path = self.checkpoint_dir / "results" / f"{job_id}_results.json"
            if results_path.exists():
                results_path.unlink()
            
            return True
            
        except Exception as e:
            print(f"Error deleting job checkpoint {job_id}: {e}")
            return False
    
    def cleanup_old_checkpoints(self, days_old: int = 30) -> int:
        """Clean up checkpoints older than specified days"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cleaned_count = 0
            
            for job_file in (self.checkpoint_dir / "jobs").glob("*.json"):
                if job_file.stat().st_mtime < cutoff_date.timestamp():
                    job_id = job_file.stem
                    if self.delete_job_checkpoint(job_id):
                        cleaned_count += 1
            
            return cleaned_count
            
        except Exception as e:
            print(f"Error cleaning up old checkpoints: {e}")
            return 0
    
    def get_checkpoint_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of available checkpoints for a job"""
        status = {
            "job_metadata": False,
            "data_checkpoints": [],
            "results": False,
            "total_size_mb": 0
        }
        
        try:
            # Check job metadata
            job_path = self.checkpoint_dir / "jobs" / f"{job_id}.json"
            if job_path.exists():
                status["job_metadata"] = True
                status["total_size_mb"] += job_path.stat().st_size / (1024 * 1024)
            
            # Check data checkpoints
            data_dir = self.checkpoint_dir / "data"
            for data_file in data_dir.glob(f"{job_id}_*.pkl"):
                step_name = data_file.stem.replace(f"{job_id}_", "")
                status["data_checkpoints"].append(step_name)
                status["total_size_mb"] += data_file.stat().st_size / (1024 * 1024)
            
            # Check results
            results_path = self.checkpoint_dir / "results" / f"{job_id}_results.json"
            if results_path.exists():
                status["results"] = True
                status["total_size_mb"] += results_path.stat().st_size / (1024 * 1024)
            
            status["total_size_mb"] = round(status["total_size_mb"], 2)
            
        except Exception as e:
            print(f"Error getting checkpoint status for {job_id}: {e}")
        
        return status
    
    def _make_serializable(self, obj: Any) -> Any:
        """Make object JSON serializable"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, pd.Series):
            return obj.to_list()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return self._make_serializable(obj.__dict__)
        else:
            try:
                json.dumps(obj)  # Test if it's already serializable
                return obj
            except:
                return str(obj)  # Fallback to string representation
    
    def get_disk_usage(self) -> Dict[str, float]:
        """Get disk usage statistics for checkpoints"""
        usage = {
            "jobs_mb": 0,
            "data_mb": 0, 
            "results_mb": 0,
            "total_mb": 0
        }
        
        try:
            # Jobs directory
            jobs_dir = self.checkpoint_dir / "jobs"
            if jobs_dir.exists():
                for file in jobs_dir.iterdir():
                    usage["jobs_mb"] += file.stat().st_size / (1024 * 1024)
            
            # Data directory
            data_dir = self.checkpoint_dir / "data"
            if data_dir.exists():
                for file in data_dir.iterdir():
                    usage["data_mb"] += file.stat().st_size / (1024 * 1024)
            
            # Results directory
            results_dir = self.checkpoint_dir / "results"
            if results_dir.exists():
                for file in results_dir.iterdir():
                    usage["results_mb"] += file.stat().st_size / (1024 * 1024)
            
            # Round to 2 decimal places
            for key in usage:
                usage[key] = round(usage[key], 2)
            
            usage["total_mb"] = usage["jobs_mb"] + usage["data_mb"] + usage["results_mb"]
            
        except Exception as e:
            print(f"Error calculating disk usage: {e}")
        
        return usage