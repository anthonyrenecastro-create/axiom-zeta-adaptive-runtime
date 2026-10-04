#ifndef QUADRA_KERNEL_HPP
#define QUADRA_KERNEL_HPP

#include <vector>
#include <memory>
#include <atomic>
#include <mutex>
#include <cstdint>
#include <array>

namespace quadra {

// Configuration constants for embedded systems
constexpr size_t MAX_FIELD_SIZE = 512;
constexpr size_t MAX_NEURONS = 256;
constexpr size_t MAX_BATCH_SIZE = 16;
constexpr float STABILITY_THRESHOLD = 0.05f;

// Real-time processing priorities
enum class ProcessPriority {
    CRITICAL = 0,  // Drone stabilization, collision avoidance
    HIGH = 1,      // Navigation, sensor fusion
    NORMAL = 2,    // AI inference, learning
    LOW = 3        // Logging, telemetry
};

// Kernel status codes
enum class KernelStatus {
    OK = 0,
    ERROR_INIT = -1,
    ERROR_MEMORY = -2,
    ERROR_TIMEOUT = -3,
    ERROR_INVALID_INPUT = -4,
    ERROR_OVERFLOW = -5
};

// Forward declarations
class SNNKernel;
class FieldManager;
class RealtimeScheduler;

/**
 * @brief Core Spiking Neural Network Kernel for embedded systems
 * 
 * Optimized for real-time drone control and low-power operation
 */
class SNNKernel {
public:
    struct Config {
        size_t field_size = 100;
        size_t num_neurons = 128;
        float learning_rate = 0.001f;
        bool use_hardware_acceleration = true;
        uint32_t max_inference_time_us = 1000; // 1ms deadline
    };

    SNNKernel(const Config& config);
    ~SNNKernel();

    // Initialization
    KernelStatus initialize();
    KernelStatus shutdown();
    
    // Real-time inference (hard deadline)
    KernelStatus infer(const float* input, size_t input_size, 
                      float* output, size_t output_size,
                      uint64_t deadline_us = 0);
    
    // Learning (can be preempted)
    KernelStatus train(const float* data, size_t data_size, 
                      const char* label, size_t label_size,
                      uint32_t epochs = 1);
    
    // Field state management
    KernelStatus get_field_state(float* state, size_t* state_size) const;
    KernelStatus set_field_state(const float* state, size_t state_size);
    
    // Statistics and monitoring
    struct Stats {
        uint64_t total_inferences = 0;
        uint64_t total_spikes = 0;
        float avg_inference_time_us = 0.0f;
        float field_variance = 0.0f;
        float syntropy_level = 0.0f;
        uint32_t missed_deadlines = 0;
    };
    
    Stats get_stats() const;
    void reset_stats();
    
    // Thread-safe state access
    bool is_stable() const;
    float get_field_resonance() const;

private:
    Config config_;
    std::unique_ptr<FieldManager> field_manager_;
    std::unique_ptr<RealtimeScheduler> scheduler_;
    
    mutable std::mutex state_mutex_;
    std::atomic<bool> initialized_{false};
    std::atomic<bool> running_{false};
    
    Stats stats_;
    
    // Internal processing
    void process_spike_train(const float* spikes, size_t num_spikes);
    void update_field(const float* delta);
    float compute_resonance() const;
};

/**
 * @brief Field state manager for quantum-inspired dynamics
 */
class FieldManager {
public:
    FieldManager(size_t field_size);
    ~FieldManager();
    
    void update(const float* delta, size_t size);
    void get_state(float* output, size_t* size) const;
    void set_state(const float* input, size_t size);
    
    float compute_variance() const;
    float compute_resonance() const;
    void apply_vibrational_mode(const float* mode, size_t size);
    
private:
    std::vector<float> field_data_;
    std::vector<float> oscillation_phase_;
    size_t field_size_;
    mutable std::mutex field_mutex_;
};

/**
 * @brief Real-time scheduler for time-critical drone operations
 */
class RealtimeScheduler {
public:
    RealtimeScheduler();
    ~RealtimeScheduler();
    
    bool schedule_task(ProcessPriority priority, 
                      std::function<void()> task,
                      uint64_t deadline_us = 0);
    
    void run();
    void stop();
    
    uint32_t get_missed_deadlines() const;
    
private:
    std::atomic<bool> running_{false};
    std::atomic<uint32_t> missed_deadlines_{0};
};

/**
 * @brief Drone controller integration interface
 */
class DroneKernelInterface {
public:
    struct DroneState {
        float position[3];      // x, y, z (meters)
        float velocity[3];      // vx, vy, vz (m/s)
        float orientation[4];   // quaternion (w, x, y, z)
        float angular_vel[3];   // roll, pitch, yaw rates (rad/s)
        uint64_t timestamp_us;
    };
    
    struct ControlOutput {
        float throttle;         // [0.0, 1.0]
        float roll;            // [-1.0, 1.0]
        float pitch;           // [-1.0, 1.0]
        float yaw;             // [-1.0, 1.0]
        bool emergency_stop;
    };
    
    DroneKernelInterface(SNNKernel* kernel);
    ~DroneKernelInterface();
    
    // Real-time control loop (must run at 1kHz+)
    KernelStatus process_control_cycle(const DroneState& state,
                                       ControlOutput& output);
    
    // Sensor fusion with AI
    KernelStatus fuse_sensor_data(const float* imu_data, size_t imu_size,
                                  const float* vision_data, size_t vision_size,
                                  DroneState& fused_state);
    
    // Collision avoidance with SNN
    bool detect_collision_risk(const float* obstacle_data, size_t data_size,
                              float& risk_score);
    
    // Adaptive flight controller
    void update_pid_gains(const DroneState& state);
    
private:
    SNNKernel* kernel_;
    std::array<float, MAX_FIELD_SIZE> control_buffer_;
    
    // PID state
    struct PIDState {
        float integral[3] = {0, 0, 0};
        float prev_error[3] = {0, 0, 0};
        float kp = 1.0f, ki = 0.1f, kd = 0.05f;
    } pid_state_;
};

/**
 * @brief Memory-mapped kernel interface for direct hardware access
 */
class KernelMemoryInterface {
public:
    static KernelMemoryInterface& instance();
    
    // Memory-mapped register access
    void write_register(uint32_t offset, uint32_t value);
    uint32_t read_register(uint32_t offset);
    
    // DMA transfer support
    KernelStatus dma_transfer(const void* src, void* dst, size_t size);
    
    // Hardware acceleration hooks
    bool has_snn_accelerator() const;
    KernelStatus offload_inference(const float* input, size_t size,
                                   float* output);
    
private:
    KernelMemoryInterface();
    ~KernelMemoryInterface();
    
    void* mmio_base_ = nullptr;
    bool hardware_accel_available_ = false;
};

} // namespace quadra

#endif // QUADRA_KERNEL_HPP
