"""
Tests for model monitoring
"""
import pytest
import time
import numpy as np
from pathlib import Path
from utils.model_monitoring import (
    ModelMonitor,
    HealthChecker,
    PredictionMetrics,
    DriftMetrics
)


@pytest.fixture
def tmp_monitoring_dir(tmp_path):
    """Create temporary monitoring directory"""
    return tmp_path / "monitoring"


@pytest.fixture
def monitor(tmp_monitoring_dir):
    """Create model monitor"""
    return ModelMonitor(
        monitoring_dir=tmp_monitoring_dir,
        window_size=100,
        drift_threshold=2.0
    )


def test_monitor_init(monitor, tmp_monitoring_dir):
    """Test monitor initialization"""
    assert monitor.monitoring_dir == tmp_monitoring_dir
    assert tmp_monitoring_dir.exists()
    assert monitor.total_predictions == 0


def test_record_prediction(monitor):
    """Test recording predictions"""
    monitor.record_prediction(
        input_data={'test': 'data'},
        prediction_time=0.1,
        confidence=0.9,
        success=True
    )
    
    assert monitor.total_predictions == 1
    assert len(monitor.prediction_times) == 1
    assert len(monitor.confidences) == 1


def test_record_failed_prediction(monitor):
    """Test recording failed predictions"""
    monitor.record_prediction(
        input_data={'test': 'data'},
        prediction_time=0.5,
        success=False,
        error="Model error"
    )
    
    assert monitor.error_count == 1


def test_get_statistics(monitor):
    """Test getting statistics"""
    # Record some predictions
    for i in range(10):
        monitor.record_prediction(
            input_data={'idx': i},
            prediction_time=0.1 + i * 0.01,
            confidence=0.8 + i * 0.01
        )
    
    stats = monitor.get_statistics()
    
    assert stats['total_predictions'] == 10
    assert 'prediction_time' in stats
    assert 'confidence' in stats
    assert stats['prediction_time']['mean'] > 0
    assert stats['confidence']['mean'] > 0.8


def test_set_baseline(monitor):
    """Test setting baseline metrics"""
    # Record predictions
    for i in range(50):
        monitor.record_prediction(
            input_data={'idx': i},
            prediction_time=0.1,
            confidence=0.85 + np.random.normal(0, 0.05)
        )
    
    monitor.set_baseline()
    
    assert monitor.baseline_metrics is not None
    assert monitor.baseline_metrics.sample_count == 50
    assert 0.7 < monitor.baseline_metrics.mean < 1.0


def test_drift_detection_no_drift(monitor):
    """Test drift detection with no drift"""
    # Set baseline
    for i in range(50):
        monitor.record_prediction(
            input_data={'idx': i},
            prediction_time=0.1,
            confidence=0.85 + np.random.normal(0, 0.05)
        )
    monitor.set_baseline()
    
    # Record similar predictions
    monitor.confidences.clear()
    for i in range(50):
        monitor.record_prediction(
            input_data={'idx': i},
            prediction_time=0.1,
            confidence=0.85 + np.random.normal(0, 0.05)
        )
    
    result = monitor.detect_drift()
    assert result['drift_detected'] is False


def test_drift_detection_with_drift(monitor):
    """Test drift detection with actual drift"""
    # Set baseline with high confidence
    for i in range(50):
        monitor.record_prediction(
            input_data={'idx': i},
            prediction_time=0.1,
            confidence=0.9 + np.random.normal(0, 0.02)
        )
    monitor.set_baseline()
    
    # Record low confidence predictions (drift)
    monitor.confidences.clear()
    for i in range(50):
        monitor.record_prediction(
            input_data={'idx': i},
            prediction_time=0.1,
            confidence=0.5 + np.random.normal(0, 0.02)
        )
    
    result = monitor.detect_drift()
    assert result['drift_detected'] is True
    assert result['drift_score'] > result['threshold']


def test_health_checker(tmp_path):
    """Test health checker"""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    
    # Create required files
    (model_dir / "model.pth").touch()
    (model_dir / "config.json").touch()
    
    checker = HealthChecker(
        model_path=model_dir,
        required_files=["model.pth", "config.json"]
    )
    
    health = checker.check_health()
    
    assert health['healthy'] is True
    assert health['model_dir_exists'] is True
    assert health['required_files']['model.pth'] is True


def test_health_checker_missing_files(tmp_path):
    """Test health checker with missing files"""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    
    checker = HealthChecker(
        model_path=model_dir,
        required_files=["model.pth", "config.json"]
    )
    
    health = checker.check_health()
    
    assert health['healthy'] is False
    assert health['required_files']['model.pth'] is False


def test_reset_counters(monitor):
    """Test resetting counters"""
    # Record predictions
    for i in range(10):
        monitor.record_prediction(
            input_data={'idx': i},
            prediction_time=0.1,
            confidence=0.9
        )
    
    assert monitor.total_predictions == 10
    
    monitor.reset_counters()
    
    assert monitor.total_predictions == 0
    assert len(monitor.prediction_times) == 0
