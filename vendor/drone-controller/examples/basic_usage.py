"""
Example: Basic SNN Kernel Usage
Demonstrates initialization, inference, and training
"""

import numpy as np
from kernel.quadra_kernel import QuadraKernel, KernelConfig


def main():
    print("=" * 60)
    print("Quadra Matrix SNN Kernel - Basic Example")
    print("=" * 60)
    
    # Configure kernel
    config = KernelConfig(
        field_size=100,
        num_neurons=128,
        learning_rate=0.001,
        use_hardware_acceleration=False  # Disable for compatibility
    )
    
    print("\n1. Creating and initializing kernel...")
    kernel = QuadraKernel(config)
    
    if kernel.initialize():
        print("   ✓ Kernel initialized successfully")
    else:
        print("   ✗ Kernel initialization failed")
        return
    
    # Test inference
    print("\n2. Running inference...")
    input_data = np.random.randn(16).astype(np.float32)
    print(f"   Input shape: {input_data.shape}")
    print(f"   Input (first 5): {input_data[:5]}")
    
    success, output = kernel.infer(input_data, output_size=4, deadline_us=1000)
    
    if success:
        print(f"   ✓ Inference successful")
        print(f"   Output: {output}")
    else:
        print(f"   ✗ Inference failed or deadline missed")
    
    # Run multiple inferences to gather statistics
    print("\n3. Running batch inference (100 iterations)...")
    for i in range(100):
        input_data = np.random.randn(16).astype(np.float32)
        success, output = kernel.infer(input_data, output_size=4)
        if not success:
            print(f"   Warning: Inference {i} failed")
    
    # Get statistics
    print("\n4. Performance Statistics:")
    stats = kernel.get_stats()
    print(f"   Total inferences: {stats['total_inferences']}")
    print(f"   Avg inference time: {stats['avg_inference_time_us']:.2f} µs")
    print(f"   Field variance: {stats['field_variance']:.6f}")
    print(f"   Syntropy level: {stats['syntropy_level']:.6f}")
    print(f"   Missed deadlines: {stats['missed_deadlines']}")
    
    # Training
    print("\n5. Training the kernel...")
    training_data = np.random.randn(50).astype(np.float32)
    
    if kernel.train(training_data, label="pattern_a", epochs=10):
        print("   ✓ Training successful")
    else:
        print("   ✗ Training failed")
    
    # Check field state
    print("\n6. Field State Analysis:")
    field_state = kernel.get_field_state()
    print(f"   Field size: {len(field_state)}")
    print(f"   Field mean: {np.mean(field_state):.6f}")
    print(f"   Field std: {np.std(field_state):.6f}")
    print(f"   Field stable: {kernel.is_stable()}")
    print(f"   Field resonance: {kernel.get_field_resonance():.6f}")
    
    # Shutdown
    print("\n7. Shutting down...")
    if kernel.shutdown():
        print("   ✓ Kernel shutdown successful")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
