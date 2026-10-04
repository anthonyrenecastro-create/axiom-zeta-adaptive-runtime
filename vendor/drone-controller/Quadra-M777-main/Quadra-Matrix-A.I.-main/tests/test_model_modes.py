"""
Tests for model modes
"""
import pytest
from utils.model_modes import (
    ModelMode,
    ModelModeManager,
    InferenceGuard,
    TrainingGuard,
    require_mode,
    inference_only,
    training_only
)


@pytest.fixture
def mode_manager():
    """Create mode manager"""
    return ModelModeManager(initial_mode=ModelMode.INFERENCE)


def test_initial_mode(mode_manager):
    """Test initial mode"""
    assert mode_manager.mode == ModelMode.INFERENCE
    assert mode_manager.is_inference_mode() is True
    assert mode_manager.is_training_mode() is False


def test_set_mode(mode_manager):
    """Test setting mode"""
    mode_manager.set_mode(ModelMode.TRAINING)
    
    assert mode_manager.mode == ModelMode.TRAINING
    assert mode_manager.is_training_mode() is True
    assert mode_manager.is_inference_mode() is False


def test_enter_inference_mode(mode_manager):
    """Test entering inference mode"""
    mode_manager.set_mode(ModelMode.TRAINING)
    mode_manager.enter_inference_mode()
    
    assert mode_manager.is_inference_mode() is True


def test_enter_training_mode(mode_manager):
    """Test entering training mode"""
    mode_manager.enter_training_mode()
    
    assert mode_manager.is_training_mode() is True


def test_enter_maintenance_mode(mode_manager):
    """Test entering maintenance mode"""
    mode_manager.enter_maintenance_mode()
    
    assert mode_manager.is_maintenance_mode() is True


def test_mode_callbacks(mode_manager):
    """Test mode change callbacks"""
    callback_called = []
    
    def callback():
        callback_called.append(True)
    
    mode_manager.register_callback(ModelMode.TRAINING, callback)
    mode_manager.set_mode(ModelMode.TRAINING)
    
    assert len(callback_called) == 1


def test_inference_guard_success(mode_manager):
    """Test inference guard in inference mode"""
    mode_manager.set_mode(ModelMode.INFERENCE)
    
    with InferenceGuard(mode_manager):
        # Should not raise
        pass


def test_inference_guard_failure(mode_manager):
    """Test inference guard in non-inference mode"""
    mode_manager.set_mode(ModelMode.TRAINING)
    
    with pytest.raises(RuntimeError, match="Cannot perform inference"):
        with InferenceGuard(mode_manager):
            pass


def test_training_guard_success(mode_manager):
    """Test training guard in training mode"""
    mode_manager.set_mode(ModelMode.TRAINING)
    
    with TrainingGuard(mode_manager):
        # Should not raise
        pass


def test_training_guard_failure(mode_manager):
    """Test training guard in non-training mode"""
    mode_manager.set_mode(ModelMode.INFERENCE)
    
    with pytest.raises(RuntimeError, match="Cannot perform training"):
        with TrainingGuard(mode_manager):
            pass


def test_mode_manager_already_in_mode(mode_manager, caplog):
    """Test setting mode when already in that mode"""
    mode_manager.set_mode(ModelMode.INFERENCE)
    mode_manager.enter_inference_mode()
    
    assert "Already in inference mode" in caplog.text


def test_multiple_mode_transitions(mode_manager):
    """Test multiple mode transitions"""
    assert mode_manager.is_inference_mode()
    
    mode_manager.enter_training_mode()
    assert mode_manager.is_training_mode()
    
    mode_manager.enter_maintenance_mode()
    assert mode_manager.is_maintenance_mode()
    
    mode_manager.enter_inference_mode()
    assert mode_manager.is_inference_mode()
