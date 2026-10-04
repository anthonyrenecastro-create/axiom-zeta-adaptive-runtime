"""
Quadra Matrix SNN Kernel - Python Wrapper
High-level Python API for drone controller integration
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
import time

try:
    from . import quadra_kernel_py as _kernel
except ImportError:
    # Fallback for development without compiled extension
    print("Warning: C++ kernel not available, using Python simulation mode")
    _kernel = None


@dataclass
class KernelConfig:
    """Configuration for SNN Kernel"""
    field_size: int = 100
    num_neurons: int = 128
    learning_rate: float = 0.001
    use_hardware_acceleration: bool = True
    max_inference_time_us: int = 1000


@dataclass
class DroneState:
    """Drone state vector"""
    position: np.ndarray  # [x, y, z] meters
    velocity: np.ndarray  # [vx, vy, vz] m/s
    orientation: np.ndarray  # [w, x, y, z] quaternion
    angular_velocity: np.ndarray  # [roll, pitch, yaw] rad/s
    timestamp_us: int = 0


@dataclass
class ControlOutput:
    """Control signals for drone"""
    throttle: float = 0.0  # [0.0, 1.0]
    roll: float = 0.0  # [-1.0, 1.0]
    pitch: float = 0.0  # [-1.0, 1.0]
    yaw: float = 0.0  # [-1.0, 1.0]
    emergency_stop: bool = False


class QuadraKernel:
    """
    High-level Python interface to Quadra Matrix SNN Kernel
    
    Example:
        >>> config = KernelConfig(field_size=100, num_neurons=128)
        >>> kernel = QuadraKernel(config)
        >>> kernel.initialize()
        >>> 
        >>> # Inference
        >>> input_data = np.random.randn(16)
        >>> output = kernel.infer(input_data, output_size=4)
        >>> 
        >>> # Training
        >>> kernel.train(input_data, label="pattern_a", epochs=10)
        >>> 
        >>> # Get statistics
        >>> stats = kernel.get_stats()
        >>> print(f"Total inferences: {stats['total_inferences']}")
    """
    
    def __init__(self, config: Optional[KernelConfig] = None):
        self.config = config or KernelConfig()
        
        if _kernel:
            self._cpp_config = _kernel.KernelConfig()
            self._cpp_config.field_size = self.config.field_size
            self._cpp_config.num_neurons = self.config.num_neurons
            self._cpp_config.learning_rate = self.config.learning_rate
            self._cpp_config.use_hardware_acceleration = self.config.use_hardware_acceleration
            self._cpp_config.max_inference_time_us = self.config.max_inference_time_us
            
            self._kernel = _kernel.SNNKernel(self._cpp_config)
        else:
            self._kernel = None
            self._field_state = np.random.randn(self.config.field_size) * 0.1
            self._stats = {
                'total_inferences': 0,
                'total_spikes': 0,
                'avg_inference_time_us': 0.0,
                'field_variance': 0.0,
                'syntropy_level': 0.0,
                'missed_deadlines': 0
            }
    
    def initialize(self) -> bool:
        """Initialize the kernel"""
        if self._kernel:
            status = self._kernel.initialize()
            return status == _kernel.KernelStatus.OK
        return True
    
    def shutdown(self) -> bool:
        """Shutdown the kernel"""
        if self._kernel:
            status = self._kernel.shutdown()
            return status == _kernel.KernelStatus.OK
        return True
    
    def infer(self, 
              input_data: np.ndarray,
              output_size: int = 4,
              deadline_us: int = 0) -> Tuple[bool, np.ndarray]:
        """
        Run inference on input data
        
        Args:
            input_data: Input array (will be converted to float32)
            output_size: Size of output array
            deadline_us: Maximum inference time in microseconds (0 = no limit)
            
        Returns:
            (success, output_array)
        """
        input_data = np.asarray(input_data, dtype=np.float32)
        
        if self._kernel:
            status, output = self._kernel.infer(input_data, output_size, deadline_us)
            return (status == _kernel.KernelStatus.OK, np.array(output))
        else:
            # Python simulation
            start_time = time.time()
            
            # Simple feed-forward simulation
            output = np.tanh(self._field_state[:output_size] + 
                           np.mean(input_data) * 0.1)
            
            elapsed_us = (time.time() - start_time) * 1e6
            self._stats['total_inferences'] += 1
            self._stats['avg_inference_time_us'] = (
                (self._stats['avg_inference_time_us'] * (self._stats['total_inferences'] - 1) + elapsed_us) /
                self._stats['total_inferences']
            )
            
            if deadline_us > 0 and elapsed_us > deadline_us:
                self._stats['missed_deadlines'] += 1
                return (False, output)
            
            return (True, output)
    
    def train(self,
              data: np.ndarray,
              label: str = "",
              epochs: int = 1) -> bool:
        """
        Train the kernel on data
        
        Args:
            data: Training data array
            label: Optional label for the data
            epochs: Number of training epochs
            
        Returns:
            success
        """
        data = np.asarray(data, dtype=np.float32)
        
        if self._kernel:
            status = self._kernel.train(data, label, epochs)
            return status == _kernel.KernelStatus.OK
        else:
            # Python simulation - simple gradient update
            for _ in range(epochs):
                update = data[:len(self._field_state)] * self.config.learning_rate
                self._field_state += update[:self.config.field_size]
                self._field_state = np.clip(self._field_state, -10, 10)
            return True
    
    def get_field_state(self) -> np.ndarray:
        """Get current field state"""
        if self._kernel:
            status, state = self._kernel.get_field_state()
            return np.array(state) if status == _kernel.KernelStatus.OK else np.array([])
        else:
            return self._field_state.copy()
    
    def set_field_state(self, state: np.ndarray) -> bool:
        """Set field state"""
        state = np.asarray(state, dtype=np.float32)
        
        if self._kernel:
            status = self._kernel.set_field_state(state)
            return status == _kernel.KernelStatus.OK
        else:
            self._field_state = state[:self.config.field_size].copy()
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get kernel statistics"""
        if self._kernel:
            cpp_stats = self._kernel.get_stats()
            return {
                'total_inferences': cpp_stats.total_inferences,
                'total_spikes': cpp_stats.total_spikes,
                'avg_inference_time_us': cpp_stats.avg_inference_time_us,
                'field_variance': cpp_stats.field_variance,
                'syntropy_level': cpp_stats.syntropy_level,
                'missed_deadlines': cpp_stats.missed_deadlines
            }
        else:
            self._stats['field_variance'] = float(np.var(self._field_state))
            self._stats['syntropy_level'] = float(np.mean(np.abs(np.diff(self._field_state))))
            return self._stats.copy()
    
    def reset_stats(self):
        """Reset statistics"""
        if self._kernel:
            self._kernel.reset_stats()
        else:
            self._stats = {k: 0 if k != 'avg_inference_time_us' else 0.0 
                          for k in self._stats}
    
    def is_stable(self) -> bool:
        """Check if field is stable"""
        if self._kernel:
            return self._kernel.is_stable()
        else:
            return np.var(self._field_state) < 0.05
    
    def get_field_resonance(self) -> float:
        """Get field resonance level"""
        if self._kernel:
            return self._kernel.get_field_resonance()
        else:
            return float(np.mean(np.abs(np.correlate(self._field_state, self._field_state, mode='valid'))))


class DroneController:
    """
    High-level drone controller interface using SNN kernel
    
    Example:
        >>> kernel = QuadraKernel()
        >>> kernel.initialize()
        >>> controller = DroneController(kernel)
        >>> 
        >>> # Control loop
        >>> state = DroneState(
        ...     position=np.array([0.0, 0.0, 1.0]),
        ...     velocity=np.array([0.0, 0.0, 0.0]),
        ...     orientation=np.array([1.0, 0.0, 0.0, 0.0]),
        ...     angular_velocity=np.array([0.0, 0.0, 0.0])
        ... )
        >>> control = controller.compute_control(state)
        >>> print(f"Throttle: {control.throttle}, Roll: {control.roll}")
    """
    
    def __init__(self, kernel: QuadraKernel):
        self.kernel = kernel
        
        if _kernel and kernel._kernel:
            self._interface = _kernel.DroneKernelInterface(kernel._kernel)
        else:
            self._interface = None
    
    def compute_control(self, state: DroneState) -> ControlOutput:
        """
        Compute control output from drone state
        
        Args:
            state: Current drone state
            
        Returns:
            Control output
        """
        if self._interface:
            # Use C++ implementation
            cpp_state = _kernel.DroneState()
            cpp_state.position = state.position
            cpp_state.velocity = state.velocity
            cpp_state.orientation = state.orientation
            cpp_state.angular_vel = state.angular_velocity
            cpp_state.timestamp_us = state.timestamp_us
            
            output = _kernel.ControlOutput()
            status = self._interface.process_control_cycle(cpp_state, output)
            
            return ControlOutput(
                throttle=output.throttle,
                roll=output.roll,
                pitch=output.pitch,
                yaw=output.yaw,
                emergency_stop=output.emergency_stop
            )
        else:
            # Python simulation
            input_vec = np.concatenate([
                state.position,
                state.velocity,
                state.orientation,
                state.angular_velocity
            ])
            
            # Normalize
            input_vec = np.tanh(input_vec * 0.1) * 0.5 + 0.5
            
            # Infer
            success, output = self.kernel.infer(input_vec, output_size=4, deadline_us=1000)
            
            if not success:
                return ControlOutput(
                    throttle=0.5,
                    roll=0.0,
                    pitch=0.0,
                    yaw=0.0,
                    emergency_stop=True
                )
            
            return ControlOutput(
                throttle=float(np.clip(output[0], 0.0, 1.0)),
                roll=float(np.clip(output[1], -1.0, 1.0)),
                pitch=float(np.clip(output[2], -1.0, 1.0)),
                yaw=float(np.clip(output[3], -1.0, 1.0)),
                emergency_stop=False
            )
    
    def fuse_sensors(self,
                    imu_data: np.ndarray,
                    vision_data: np.ndarray) -> Tuple[bool, DroneState]:
        """
        Fuse IMU and vision sensor data
        
        Args:
            imu_data: IMU sensor readings
            vision_data: Vision/camera data
            
        Returns:
            (success, fused_state)
        """
        imu_data = np.asarray(imu_data, dtype=np.float32)
        vision_data = np.asarray(vision_data, dtype=np.float32)
        
        if self._interface:
            status, cpp_state = self._interface.fuse_sensor_data(imu_data, vision_data)
            
            state = DroneState(
                position=np.array(cpp_state.position),
                velocity=np.array(cpp_state.velocity),
                orientation=np.array(cpp_state.orientation),
                angular_velocity=np.array(cpp_state.angular_vel),
                timestamp_us=cpp_state.timestamp_us
            )
            
            return (status == _kernel.KernelStatus.OK, state)
        else:
            # Python simulation
            combined = np.concatenate([imu_data, vision_data])
            success, output = self.kernel.infer(combined, output_size=13)
            
            if not success:
                return (False, DroneState(
                    position=np.zeros(3),
                    velocity=np.zeros(3),
                    orientation=np.array([1, 0, 0, 0]),
                    angular_velocity=np.zeros(3)
                ))
            
            state = DroneState(
                position=output[0:3],
                velocity=output[3:6],
                orientation=output[6:10],
                angular_velocity=output[10:13],
                timestamp_us=int(time.time() * 1e6)
            )
            
            return (True, state)
    
    def detect_collision(self, obstacle_data: np.ndarray) -> Tuple[bool, float]:
        """
        Detect collision risk from obstacle data
        
        Args:
            obstacle_data: Distance/obstacle sensor data
            
        Returns:
            (at_risk, risk_score)
        """
        obstacle_data = np.asarray(obstacle_data, dtype=np.float32)
        
        if self._interface:
            return self._interface.detect_collision_risk(obstacle_data)
        else:
            # Python simulation
            success, output = self.kernel.infer(obstacle_data, output_size=1, deadline_us=500)
            risk_score = float(np.clip(output[0], 0.0, 1.0)) if success else 1.0
            return (risk_score > 0.7, risk_score)


# Convenience functions
def create_kernel(field_size: int = 100, 
                 num_neurons: int = 128,
                 learning_rate: float = 0.001) -> QuadraKernel:
    """Create and initialize a kernel with given parameters"""
    config = KernelConfig(
        field_size=field_size,
        num_neurons=num_neurons,
        learning_rate=learning_rate
    )
    kernel = QuadraKernel(config)
    kernel.initialize()
    return kernel


def create_drone_controller(kernel: Optional[QuadraKernel] = None) -> DroneController:
    """Create a drone controller (creates kernel if not provided)"""
    if kernel is None:
        kernel = create_kernel()
    return DroneController(kernel)


__all__ = [
    'QuadraKernel',
    'DroneController',
    'KernelConfig',
    'DroneState',
    'ControlOutput',
    'create_kernel',
    'create_drone_controller'
]
