"""
Model serving modes: inference vs training boundaries
"""
import logging
import threading
from enum import Enum
from typing import Optional, Callable
from functools import wraps
from flask import jsonify

logger = logging.getLogger(__name__)


class ModelMode(Enum):
    """Model serving modes"""
    INFERENCE = "inference"
    TRAINING = "training"
    MAINTENANCE = "maintenance"


class ModelModeManager:
    """Manage model serving mode"""
    
    def __init__(self, initial_mode: ModelMode = ModelMode.INFERENCE):
        """
        Initialize mode manager
        
        Args:
            initial_mode: Starting mode
        """
        self._mode = initial_mode
        self._lock = threading.RLock()
        self._mode_callbacks = {mode: [] for mode in ModelMode}
        logger.info(f"Model mode initialized: {initial_mode.value}")
    
    @property
    def mode(self) -> ModelMode:
        """Get current mode"""
        with self._lock:
            return self._mode
    
    def set_mode(self, mode: ModelMode):
        """
        Set model mode
        
        Args:
            mode: New mode to set
        """
        with self._lock:
            old_mode = self._mode
            self._mode = mode
            logger.info(f"Model mode changed: {old_mode.value} -> {mode.value}")
            
            # Execute callbacks
            for callback in self._mode_callbacks[mode]:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Mode callback error: {e}")
    
    def is_inference_mode(self) -> bool:
        """Check if in inference mode"""
        return self.mode == ModelMode.INFERENCE
    
    def is_training_mode(self) -> bool:
        """Check if in training mode"""
        return self.mode == ModelMode.TRAINING
    
    def is_maintenance_mode(self) -> bool:
        """Check if in maintenance mode"""
        return self.mode == ModelMode.MAINTENANCE
    
    def register_callback(self, mode: ModelMode, callback: Callable):
        """
        Register callback for mode change
        
        Args:
            mode: Mode to trigger callback
            callback: Function to call
        """
        self._mode_callbacks[mode].append(callback)
    
    def enter_inference_mode(self):
        """Switch to inference mode"""
        if self.is_inference_mode():
            logger.info("Already in inference mode")
            return
        
        logger.info("Entering inference mode...")
        self.set_mode(ModelMode.INFERENCE)
        logger.info("Inference mode ready")
    
    def enter_training_mode(self):
        """Switch to training mode"""
        if self.is_training_mode():
            logger.info("Already in training mode")
            return
        
        logger.info("Entering training mode...")
        self.set_mode(ModelMode.TRAINING)
        logger.info("Training mode ready")
    
    def enter_maintenance_mode(self):
        """Switch to maintenance mode"""
        if self.is_maintenance_mode():
            logger.info("Already in maintenance mode")
            return
        
        logger.info("Entering maintenance mode...")
        self.set_mode(ModelMode.MAINTENANCE)
        logger.info("Maintenance mode active")


# Global mode manager
mode_manager = ModelModeManager()


def require_mode(*allowed_modes: ModelMode):
    """
    Decorator to require specific model mode
    
    Args:
        *allowed_modes: Modes that are allowed
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_mode = mode_manager.mode
            
            if current_mode not in allowed_modes:
                return jsonify({
                    'error': 'Operation not allowed in current mode',
                    'current_mode': current_mode.value,
                    'required_modes': [m.value for m in allowed_modes]
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def inference_only(f: Callable) -> Callable:
    """Decorator for inference-only endpoints"""
    return require_mode(ModelMode.INFERENCE)(f)


def training_only(f: Callable) -> Callable:
    """Decorator for training-only endpoints"""
    return require_mode(ModelMode.TRAINING)(f)


class InferenceGuard:
    """Context manager for inference operations"""
    
    def __init__(self, mode_manager: ModelModeManager):
        """
        Initialize inference guard
        
        Args:
            mode_manager: ModelModeManager instance
        """
        self.mode_manager = mode_manager
        self.previous_mode = None
    
    def __enter__(self):
        """Enter inference context"""
        self.previous_mode = self.mode_manager.mode
        if not self.mode_manager.is_inference_mode():
            raise RuntimeError(
                f"Cannot perform inference in {self.previous_mode.value} mode"
            )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit inference context"""
        return False  # Don't suppress exceptions


class TrainingGuard:
    """Context manager for training operations"""
    
    def __init__(self, mode_manager: ModelModeManager):
        """
        Initialize training guard
        
        Args:
            mode_manager: ModelModeManager instance
        """
        self.mode_manager = mode_manager
        self.previous_mode = None
    
    def __enter__(self):
        """Enter training context"""
        self.previous_mode = self.mode_manager.mode
        if not self.mode_manager.is_training_mode():
            raise RuntimeError(
                f"Cannot perform training in {self.previous_mode.value} mode"
            )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit training context"""
        return False  # Don't suppress exceptions
