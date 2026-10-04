"""
Example: Drone Controller Integration
Demonstrates real-time flight control using SNN kernel
"""

import numpy as np
import time
from kernel.quadra_kernel import (
    QuadraKernel, DroneController, DroneState, 
    ControlOutput, KernelConfig
)


def simulate_drone_sensors():
    """Simulate reading drone sensors"""
    # Simulate noisy sensor data
    position = np.random.randn(3) * 0.1
    velocity = np.random.randn(3) * 0.05
    orientation = np.array([1.0, 0.0, 0.0, 0.0]) + np.random.randn(4) * 0.01
    angular_velocity = np.random.randn(3) * 0.02
    
    return DroneState(
        position=position,
        velocity=velocity,
        orientation=orientation / np.linalg.norm(orientation),  # Normalize quaternion
        angular_velocity=angular_velocity,
        timestamp_us=int(time.time() * 1e6)
    )


def main():
    print("=" * 70)
    print("Quadra Matrix SNN Kernel - Drone Controller Example")
    print("=" * 70)
    
    # Create kernel with configuration optimized for drone control
    print("\n1. Initializing SNN Kernel for drone control...")
    config = KernelConfig(
        field_size=100,
        num_neurons=128,
        learning_rate=0.001,
        max_inference_time_us=1000  # 1ms deadline for 1kHz control
    )
    
    kernel = QuadraKernel(config)
    kernel.initialize()
    print("   ✓ Kernel initialized")
    
    # Create drone controller
    print("\n2. Creating drone controller interface...")
    controller = DroneController(kernel)
    print("   ✓ Controller ready")
    
    # Simulate control loop
    print("\n3. Running control loop (100 iterations @ 1kHz)...")
    print("   " + "-" * 66)
    print(f"   {'Iter':<6} {'Throttle':<10} {'Roll':<10} {'Pitch':<10} {'Yaw':<10} {'Time(µs)':<10}")
    print("   " + "-" * 66)
    
    control_times = []
    
    for i in range(100):
        start_time = time.time()
        
        # Read sensors
        state = simulate_drone_sensors()
        
        # Compute control with SNN
        control = controller.compute_control(state)
        
        elapsed_us = (time.time() - start_time) * 1e6
        control_times.append(elapsed_us)
        
        # Print every 10th iteration
        if i % 10 == 0:
            print(f"   {i:<6} {control.throttle:<10.3f} {control.roll:<10.3f} "
                  f"{control.pitch:<10.3f} {control.yaw:<10.3f} {elapsed_us:<10.1f}")
        
        # Emergency stop check
        if control.emergency_stop:
            print(f"\n   ⚠ EMERGENCY STOP at iteration {i}")
            break
        
        # Simulate 1ms cycle time
        if elapsed_us < 1000:
            time.sleep((1000 - elapsed_us) / 1e6)
    
    print("   " + "-" * 66)
    
    # Performance statistics
    print("\n4. Control Loop Performance:")
    print(f"   Total cycles: {len(control_times)}")
    print(f"   Avg cycle time: {np.mean(control_times):.2f} µs")
    print(f"   Min cycle time: {np.min(control_times):.2f} µs")
    print(f"   Max cycle time: {np.max(control_times):.2f} µs")
    print(f"   Std deviation: {np.std(control_times):.2f} µs")
    print(f"   Deadline misses: {sum(1 for t in control_times if t > 1000)}")
    
    # Sensor fusion test
    print("\n5. Testing sensor fusion...")
    imu_data = np.random.randn(6).astype(np.float32)  # ax, ay, az, gx, gy, gz
    vision_data = np.random.randn(10).astype(np.float32)  # Visual features
    
    success, fused_state = controller.fuse_sensors(imu_data, vision_data)
    
    if success:
        print("   ✓ Sensor fusion successful")
        print(f"   Position: {fused_state.position}")
        print(f"   Velocity: {fused_state.velocity}")
    else:
        print("   ✗ Sensor fusion failed")
    
    # Collision detection test
    print("\n6. Testing collision detection...")
    obstacle_distances = np.array([5.0, 3.0, 4.0, 6.0], dtype=np.float32)  # meters
    at_risk, risk_score = controller.detect_collision(obstacle_distances)
    
    print(f"   Obstacle distances: {obstacle_distances}")
    print(f"   Collision risk: {risk_score:.2%}")
    print(f"   At risk: {'YES ⚠' if at_risk else 'NO ✓'}")
    
    # Kernel statistics
    print("\n7. SNN Kernel Statistics:")
    stats = kernel.get_stats()
    print(f"   Total inferences: {stats['total_inferences']}")
    print(f"   Avg inference time: {stats['avg_inference_time_us']:.2f} µs")
    print(f"   Field variance: {stats['field_variance']:.6f}")
    print(f"   Field resonance: {stats['syntropy_level']:.6f}")
    print(f"   Missed deadlines: {stats['missed_deadlines']}")
    
    # Shutdown
    print("\n8. Shutting down...")
    kernel.shutdown()
    print("   ✓ Shutdown complete")
    
    print("\n" + "=" * 70)
    print("Drone controller example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
