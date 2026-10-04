"""
Noise Injection Module for Quadra Matrix AI
Adds various types of noise for robustness testing and adversarial training
"""

import torch
import numpy as np
import logging
from enum import Enum
from typing import Union, Tuple, Optional

logger = logging.getLogger(__name__)


class NoiseType(Enum):
    """Types of noise that can be injected"""
    GAUSSIAN = "gaussian"
    UNIFORM = "uniform"
    SALT_AND_PEPPER = "salt_and_pepper"
    DROPOUT = "dropout"
    ADVERSARIAL = "adversarial"
    QUANTIZATION = "quantization"
    FIELD_PERTURBATION = "field_perturbation"


class NoiseInjector:
    """
    Injects various types of noise into tensors, fields, and data streams
    for robustness testing and adversarial training
    """
    
    def __init__(self, enabled: bool = True, intensity: float = 0.1):
        """
        Initialize noise injector
        
        Args:
            enabled: Whether noise injection is active
            intensity: Base intensity of noise (0.0 to 1.0)
        """
        self.enabled = enabled
        self.intensity = intensity
        self.noise_stats = {
            'total_injections': 0,
            'by_type': {}
        }
        logger.info(f"NoiseInjector initialized: enabled={enabled}, intensity={intensity}")
    
    def inject(self, 
               data: Union[torch.Tensor, np.ndarray],
               noise_type: NoiseType = NoiseType.GAUSSIAN,
               intensity: Optional[float] = None) -> Union[torch.Tensor, np.ndarray]:
        """
        Inject noise into data
        
        Args:
            data: Input data (tensor or array)
            noise_type: Type of noise to inject
            intensity: Override default intensity
            
        Returns:
            Noisy data of same type as input
        """
        if not self.enabled:
            return data
        
        intensity = intensity if intensity is not None else self.intensity
        is_tensor = isinstance(data, torch.Tensor)
        
        # Convert to numpy for processing
        if is_tensor:
            device = data.device
            dtype = data.dtype
            data_np = data.cpu().numpy()
        else:
            data_np = data.copy()
        
        # Apply noise based on type
        if noise_type == NoiseType.GAUSSIAN:
            noisy_data = self._add_gaussian_noise(data_np, intensity)
        elif noise_type == NoiseType.UNIFORM:
            noisy_data = self._add_uniform_noise(data_np, intensity)
        elif noise_type == NoiseType.SALT_AND_PEPPER:
            noisy_data = self._add_salt_and_pepper(data_np, intensity)
        elif noise_type == NoiseType.DROPOUT:
            noisy_data = self._add_dropout(data_np, intensity)
        elif noise_type == NoiseType.ADVERSARIAL:
            noisy_data = self._add_adversarial_noise(data_np, intensity)
        elif noise_type == NoiseType.QUANTIZATION:
            noisy_data = self._add_quantization_noise(data_np, intensity)
        elif noise_type == NoiseType.FIELD_PERTURBATION:
            noisy_data = self._add_field_perturbation(data_np, intensity)
        else:
            noisy_data = data_np
        
        # Update statistics
        self.noise_stats['total_injections'] += 1
        self.noise_stats['by_type'][noise_type.value] = \
            self.noise_stats['by_type'].get(noise_type.value, 0) + 1
        
        # Convert back to original type
        if is_tensor:
            return torch.tensor(noisy_data, dtype=dtype, device=device)
        return noisy_data
    
    def _add_gaussian_noise(self, data: np.ndarray, intensity: float) -> np.ndarray:
        """Add Gaussian (normal) noise"""
        std = intensity * np.std(data) if np.std(data) > 0 else intensity
        noise = np.random.normal(0, std, data.shape)
        return data + noise
    
    def _add_uniform_noise(self, data: np.ndarray, intensity: float) -> np.ndarray:
        """Add uniform random noise"""
        data_range = np.ptp(data) if np.ptp(data) > 0 else 1.0
        noise = np.random.uniform(-intensity * data_range, 
                                  intensity * data_range, 
                                  data.shape)
        return data + noise
    
    def _add_salt_and_pepper(self, data: np.ndarray, intensity: float) -> np.ndarray:
        """Add salt and pepper noise (random min/max values)"""
        noisy = data.copy()
        # Salt (max value)
        salt_mask = np.random.random(data.shape) < (intensity / 2)
        noisy[salt_mask] = np.max(data)
        # Pepper (min value)
        pepper_mask = np.random.random(data.shape) < (intensity / 2)
        noisy[pepper_mask] = np.min(data)
        return noisy
    
    def _add_dropout(self, data: np.ndarray, intensity: float) -> np.ndarray:
        """Add dropout noise (randomly zero out values)"""
        mask = np.random.random(data.shape) > intensity
        return data * mask
    
    def _add_adversarial_noise(self, data: np.ndarray, intensity: float) -> np.ndarray:
        """Add adversarial perturbation (gradient-based noise)"""
        # Simulate FGSM-style perturbation
        sign = np.sign(np.gradient(data.flatten())).reshape(data.shape)
        perturbation = intensity * np.std(data) * sign
        return data + perturbation
    
    def _add_quantization_noise(self, data: np.ndarray, intensity: float) -> np.ndarray:
        """Add quantization noise (reduce precision)"""
        # More intensity = fewer quantization levels
        levels = max(2, int(256 * (1.0 - intensity)))
        data_min, data_max = np.min(data), np.max(data)
        data_normalized = (data - data_min) / (data_max - data_min + 1e-10)
        data_quantized = np.round(data_normalized * levels) / levels
        return data_quantized * (data_max - data_min) + data_min
    
    def _add_field_perturbation(self, data: np.ndarray, intensity: float) -> np.ndarray:
        """Add oscillatory field perturbation"""
        # Sinusoidal perturbation at multiple frequencies
        t = np.linspace(0, 2 * np.pi, len(data.flatten()))
        perturbation = np.zeros_like(data.flatten())
        for freq in [1.0, 2.5, 5.0]:
            perturbation += np.sin(freq * t) * intensity * 0.1
        perturbation = perturbation.reshape(data.shape)
        return data + perturbation * np.std(data)
    
    def inject_multiple(self,
                       data: Union[torch.Tensor, np.ndarray],
                       noise_types: list,
                       intensities: Optional[list] = None) -> Union[torch.Tensor, np.ndarray]:
        """
        Apply multiple noise types sequentially
        
        Args:
            data: Input data
            noise_types: List of NoiseType values
            intensities: List of intensities (one per noise type)
            
        Returns:
            Data with all noise types applied
        """
        result = data
        if intensities is None:
            intensities = [self.intensity] * len(noise_types)
        
        for noise_type, intensity in zip(noise_types, intensities):
            result = self.inject(result, noise_type, intensity)
        
        return result
    
    def set_enabled(self, enabled: bool):
        """Enable or disable noise injection"""
        self.enabled = enabled
        logger.info(f"Noise injection {'enabled' if enabled else 'disabled'}")
    
    def set_intensity(self, intensity: float):
        """Update noise intensity"""
        self.intensity = max(0.0, min(1.0, intensity))
        logger.info(f"Noise intensity set to {self.intensity}")
    
    def get_stats(self) -> dict:
        """Get noise injection statistics"""
        return self.noise_stats.copy()
    
    def reset_stats(self):
        """Reset statistics"""
        self.noise_stats = {
            'total_injections': 0,
            'by_type': {}
        }


# Convenience functions
def inject_gaussian_noise(data: Union[torch.Tensor, np.ndarray], 
                         intensity: float = 0.1) -> Union[torch.Tensor, np.ndarray]:
    """Quick Gaussian noise injection"""
    injector = NoiseInjector(enabled=True, intensity=intensity)
    return injector.inject(data, NoiseType.GAUSSIAN)


def inject_adversarial_noise(data: Union[torch.Tensor, np.ndarray],
                            intensity: float = 0.05) -> Union[torch.Tensor, np.ndarray]:
    """Quick adversarial noise injection"""
    injector = NoiseInjector(enabled=True, intensity=intensity)
    return injector.inject(data, NoiseType.ADVERSARIAL)


def create_robust_training_noise(data: Union[torch.Tensor, np.ndarray],
                                 intensity: float = 0.1) -> Union[torch.Tensor, np.ndarray]:
    """Apply multiple noise types for robust training"""
    injector = NoiseInjector(enabled=True, intensity=intensity)
    noise_types = [
        NoiseType.GAUSSIAN,
        NoiseType.DROPOUT,
        NoiseType.FIELD_PERTURBATION
    ]
    return injector.inject_multiple(data, noise_types)
