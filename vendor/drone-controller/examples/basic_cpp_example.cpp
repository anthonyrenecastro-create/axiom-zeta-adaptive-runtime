/*
 * Example: C++ Basic Usage
 * Demonstrates SNN kernel usage from C++
 */

#include "quadra_kernel.hpp"
#include <iostream>
#include <iomanip>
#include <vector>
#include <random>

using namespace quadra;

int main() {
    std::cout << std::string(60, '=') << std::endl;
    std::cout << "Quadra Matrix SNN Kernel - C++ Example" << std::endl;
    std::cout << std::string(60, '=') << std::endl;
    
    // Configure kernel
    SNNKernel::Config config;
    config.field_size = 100;
    config.num_neurons = 128;
    config.learning_rate = 0.001f;
    config.use_hardware_acceleration = false;
    config.max_inference_time_us = 1000;
    
    std::cout << "\n1. Creating and initializing kernel..." << std::endl;
    SNNKernel kernel(config);
    
    auto status = kernel.initialize();
    if (status == KernelStatus::OK) {
        std::cout << "   ✓ Kernel initialized successfully" << std::endl;
    } else {
        std::cout << "   ✗ Kernel initialization failed" << std::endl;
        return 1;
    }
    
    // Test inference
    std::cout << "\n2. Running inference..." << std::endl;
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 1.0f);
    
    std::vector<float> input(16);
    for (auto& val : input) {
        val = dist(gen);
    }
    
    std::vector<float> output(4);
    
    std::cout << "   Input (first 5): ";
    for (size_t i = 0; i < 5; ++i) {
        std::cout << std::fixed << std::setprecision(3) << input[i] << " ";
    }
    std::cout << std::endl;
    
    status = kernel.infer(input.data(), input.size(), 
                         output.data(), output.size(), 
                         1000);
    
    if (status == KernelStatus::OK) {
        std::cout << "   ✓ Inference successful" << std::endl;
        std::cout << "   Output: ";
        for (float val : output) {
            std::cout << std::fixed << std::setprecision(3) << val << " ";
        }
        std::cout << std::endl;
    } else {
        std::cout << "   ✗ Inference failed" << std::endl;
    }
    
    // Batch inference
    std::cout << "\n3. Running batch inference (1000 iterations)..." << std::endl;
    
    for (int i = 0; i < 1000; ++i) {
        for (auto& val : input) {
            val = dist(gen);
        }
        
        status = kernel.infer(input.data(), input.size(),
                            output.data(), output.size());
        
        if (status != KernelStatus::OK) {
            std::cout << "   Warning: Inference " << i << " failed" << std::endl;
        }
    }
    
    // Statistics
    std::cout << "\n4. Performance Statistics:" << std::endl;
    auto stats = kernel.get_stats();
    
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "   Total inferences: " << stats.total_inferences << std::endl;
    std::cout << "   Total spikes: " << stats.total_spikes << std::endl;
    std::cout << "   Avg inference time: " << stats.avg_inference_time_us << " µs" << std::endl;
    std::cout << std::setprecision(6);
    std::cout << "   Field variance: " << stats.field_variance << std::endl;
    std::cout << "   Syntropy level: " << stats.syntropy_level << std::endl;
    std::cout << "   Missed deadlines: " << stats.missed_deadlines << std::endl;
    
    // Training
    std::cout << "\n5. Training the kernel..." << std::endl;
    
    std::vector<float> training_data(50);
    for (auto& val : training_data) {
        val = dist(gen);
    }
    
    status = kernel.train(training_data.data(), training_data.size(),
                         "pattern_a", 9, 10);
    
    if (status == KernelStatus::OK) {
        std::cout << "   ✓ Training successful" << std::endl;
    } else {
        std::cout << "   ✗ Training failed" << std::endl;
    }
    
    // Field state
    std::cout << "\n6. Field State Analysis:" << std::endl;
    
    std::vector<float> field_state(config.field_size);
    size_t state_size = 0;
    
    status = kernel.get_field_state(field_state.data(), &state_size);
    
    if (status == KernelStatus::OK) {
        float mean = 0.0f;
        for (float val : field_state) {
            mean += val;
        }
        mean /= state_size;
        
        float variance = 0.0f;
        for (float val : field_state) {
            float diff = val - mean;
            variance += diff * diff;
        }
        variance /= state_size;
        
        std::cout << std::fixed << std::setprecision(6);
        std::cout << "   Field size: " << state_size << std::endl;
        std::cout << "   Field mean: " << mean << std::endl;
        std::cout << "   Field std: " << std::sqrt(variance) << std::endl;
        std::cout << "   Field stable: " << (kernel.is_stable() ? "YES" : "NO") << std::endl;
        std::cout << "   Field resonance: " << kernel.get_field_resonance() << std::endl;
    }
    
    // Shutdown
    std::cout << "\n7. Shutting down..." << std::endl;
    status = kernel.shutdown();
    
    if (status == KernelStatus::OK) {
        std::cout << "   ✓ Kernel shutdown successful" << std::endl;
    }
    
    std::cout << "\n" << std::string(60, '=') << std::endl;
    std::cout << "Example completed successfully!" << std::endl;
    std::cout << std::string(60, '=') << std::endl;
    
    return 0;
}
