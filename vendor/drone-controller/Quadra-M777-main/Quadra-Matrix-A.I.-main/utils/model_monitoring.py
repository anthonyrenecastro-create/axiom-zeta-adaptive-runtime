"""
Model monitoring for drift detection and failure tracking
"""
import logging
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import deque
import numpy as np
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class PredictionMetrics:
    """Metrics for a single prediction"""
    timestamp: str
    input_hash: str
    prediction_time: float
    confidence: Optional[float] = None
    success: bool = True
    error: Optional[str] = None


@dataclass
class DriftMetrics:
    """Metrics for drift detection"""
    timestamp: str
    mean: float
    std: float
    min: float
    max: float
    sample_count: int


class ModelMonitor:
    """Monitor model predictions for drift and failures"""
    
    def __init__(
        self,
        monitoring_dir: Path,
        window_size: int = 1000,
        drift_threshold: float = 2.0
    ):
        """
        Initialize model monitor
        
        Args:
            monitoring_dir: Directory for monitoring data
            window_size: Size of rolling window for metrics
            drift_threshold: Threshold for drift detection (std deviations)
        """
        self.monitoring_dir = Path(monitoring_dir)
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        
        # Rolling windows for metrics
        self.prediction_times = deque(maxlen=window_size)
        self.confidences = deque(maxlen=window_size)
        self.error_count = 0
        self.total_predictions = 0
        
        # Baseline metrics for drift detection
        self.baseline_metrics: Optional[DriftMetrics] = None
        self.current_metrics: Optional[DriftMetrics] = None
        
        # Load existing data
        self._load_monitoring_data()
    
    def _load_monitoring_data(self):
        """Load existing monitoring data"""
        metrics_file = self.monitoring_dir / "baseline_metrics.json"
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    data = json.load(f)
                self.baseline_metrics = DriftMetrics(**data)
                logger.info("Loaded baseline metrics")
            except Exception as e:
                logger.warning(f"Failed to load baseline metrics: {e}")
    
    def record_prediction(
        self,
        input_data: Any,
        prediction_time: float,
        confidence: Optional[float] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        """
        Record a prediction for monitoring
        
        Args:
            input_data: Input data (for hashing)
            prediction_time: Time taken for prediction (seconds)
            confidence: Model confidence score
            success: Whether prediction succeeded
            error: Error message if failed
        """
        self.total_predictions += 1
        
        # Record metrics
        self.prediction_times.append(prediction_time)
        if confidence is not None:
            self.confidences.append(confidence)
        
        if not success:
            self.error_count += 1
        
        # Log to file
        metrics = PredictionMetrics(
            timestamp=datetime.now().isoformat(),
            input_hash=self._hash_input(input_data),
            prediction_time=prediction_time,
            confidence=confidence,
            success=success,
            error=error
        )
        self._log_prediction(metrics)
        
        # Check for alerts
        self._check_alerts()
    
    def _hash_input(self, input_data: Any) -> str:
        """Create hash of input data"""
        import hashlib
        data_str = str(input_data).encode()
        return hashlib.md5(data_str).hexdigest()[:8]
    
    def _log_prediction(self, metrics: PredictionMetrics):
        """Log prediction metrics to file"""
        log_file = self.monitoring_dir / f"predictions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(asdict(metrics)) + '\n')
        except Exception as e:
            logger.error(f"Failed to log prediction: {e}")
    
    def _check_alerts(self):
        """Check for alerting conditions"""
        if self.total_predictions < 10:  # Need minimum data
            return
        
        # Check error rate
        error_rate = self.error_count / self.total_predictions
        if error_rate > 0.1:  # 10% error rate
            logger.warning(f"High error rate detected: {error_rate:.2%}")
        
        # Check prediction time
        if len(self.prediction_times) >= 10:
            avg_time = np.mean(list(self.prediction_times))
            if avg_time > 1.0:  # Slower than 1 second
                logger.warning(f"Slow predictions detected: {avg_time:.2f}s average")
        
        # Check confidence scores
        if len(self.confidences) >= 10:
            avg_confidence = np.mean(list(self.confidences))
            if avg_confidence < 0.5:
                logger.warning(f"Low confidence detected: {avg_confidence:.2f}")
    
    def set_baseline(self):
        """Set current metrics as baseline for drift detection"""
        if not self.confidences:
            logger.warning("No confidence scores to set as baseline")
            return
        
        confidences_array = np.array(list(self.confidences))
        
        self.baseline_metrics = DriftMetrics(
            timestamp=datetime.now().isoformat(),
            mean=float(np.mean(confidences_array)),
            std=float(np.std(confidences_array)),
            min=float(np.min(confidences_array)),
            max=float(np.max(confidences_array)),
            sample_count=len(confidences_array)
        )
        
        # Save baseline
        baseline_file = self.monitoring_dir / "baseline_metrics.json"
        with open(baseline_file, 'w') as f:
            json.dump(asdict(self.baseline_metrics), f, indent=2)
        
        logger.info(f"Baseline set with {len(confidences_array)} samples")
    
    def detect_drift(self) -> Dict[str, Any]:
        """
        Detect drift in model predictions
        
        Returns:
            Drift detection results
        """
        if not self.baseline_metrics:
            return {
                'drift_detected': False,
                'message': 'No baseline metrics set'
            }
        
        if not self.confidences:
            return {
                'drift_detected': False,
                'message': 'Insufficient current data'
            }
        
        current_confidences = np.array(list(self.confidences))
        current_mean = np.mean(current_confidences)
        
        # Calculate drift score (difference in standard deviations)
        drift_score = abs(current_mean - self.baseline_metrics.mean) / self.baseline_metrics.std
        
        drift_detected = drift_score > self.drift_threshold
        
        result = {
            'drift_detected': drift_detected,
            'drift_score': float(drift_score),
            'threshold': self.drift_threshold,
            'baseline_mean': self.baseline_metrics.mean,
            'current_mean': float(current_mean),
            'baseline_std': self.baseline_metrics.std,
            'current_std': float(np.std(current_confidences)),
            'sample_count': len(current_confidences)
        }
        
        if drift_detected:
            logger.warning(f"Drift detected! Score: {drift_score:.2f}")
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current monitoring statistics"""
        stats = {
            'total_predictions': self.total_predictions,
            'error_count': self.error_count,
            'error_rate': self.error_count / self.total_predictions if self.total_predictions > 0 else 0,
            'window_size': len(self.prediction_times)
        }
        
        if self.prediction_times:
            stats['prediction_time'] = {
                'mean': float(np.mean(list(self.prediction_times))),
                'std': float(np.std(list(self.prediction_times))),
                'min': float(np.min(list(self.prediction_times))),
                'max': float(np.max(list(self.prediction_times))),
                'p95': float(np.percentile(list(self.prediction_times), 95))
            }
        
        if self.confidences:
            stats['confidence'] = {
                'mean': float(np.mean(list(self.confidences))),
                'std': float(np.std(list(self.confidences))),
                'min': float(np.min(list(self.confidences))),
                'max': float(np.max(list(self.confidences)))
            }
        
        return stats
    
    def reset_counters(self):
        """Reset monitoring counters"""
        self.error_count = 0
        self.total_predictions = 0
        self.prediction_times.clear()
        self.confidences.clear()
        logger.info("Monitoring counters reset")


class HealthChecker:
    """Check model health and readiness"""
    
    def __init__(self, model_path: Path, required_files: List[str]):
        """
        Initialize health checker
        
        Args:
            model_path: Path to model directory
            required_files: List of required file names
        """
        self.model_path = Path(model_path)
        self.required_files = required_files
    
    def check_health(self) -> Dict[str, Any]:
        """
        Perform health check
        
        Returns:
            Health check results
        """
        checks = {}
        
        # Check model directory exists
        checks['model_dir_exists'] = self.model_path.exists()
        
        # Check required files
        checks['required_files'] = {}
        for filename in self.required_files:
            file_path = self.model_path / filename
            checks['required_files'][filename] = file_path.exists()
        
        # Check disk space
        try:
            stat = os.statvfs(self.model_path)
            free_bytes = stat.f_bavail * stat.f_frsize
            checks['disk_space_available'] = free_bytes > 1024 * 1024 * 100  # 100MB
            checks['disk_space_mb'] = free_bytes / (1024 * 1024)
        except:
            checks['disk_space_available'] = None
        
        # Overall health
        checks['healthy'] = (
            checks['model_dir_exists'] and
            all(checks['required_files'].values()) and
            checks.get('disk_space_available', True)
        )
        
        return checks
