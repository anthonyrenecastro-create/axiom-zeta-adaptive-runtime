#include "quadra_kernel.hpp"
#include <cmath>
#include <cstring>
#include <algorithm>
#include <chrono>
#include <thread>
#include <random>

namespace quadra {

// ============================================================================
// SNNKernel Implementation
// ============================================================================

SNNKernel::SNNKernel(const Config& config) 
    : config_(config) {
    field_manager_ = std::make_unique<FieldManager>(config.field_size);
    scheduler_ = std::make_unique<RealtimeScheduler>();
}

SNNKernel::~SNNKernel() {
    shutdown();
}

KernelStatus SNNKernel::initialize() {
    std::lock_guard<std::mutex> lock(state_mutex_);
    
    if (initialized_.load()) {
        return KernelStatus::OK;
    }
    
    // Initialize field state with small random values
    std::vector<float> initial_state(config_.field_size);
    std::mt19937 gen(42);
    std::normal_distribution<float> dist(0.0f, 0.1f);
    
    for (auto& val : initial_state) {
        val = dist(gen);
    }
    
    field_manager_->set_state(initial_state.data(), initial_state.size());
    
    // Reset statistics
    stats_ = Stats{};
    
    initialized_.store(true);
    running_.store(true);
    
    return KernelStatus::OK;
}

KernelStatus SNNKernel::shutdown() {
    running_.store(false);
    
    if (scheduler_) {
        scheduler_->stop();
    }
    
    initialized_.store(false);
    return KernelStatus::OK;
}

KernelStatus SNNKernel::infer(const float* input, size_t input_size,
                               float* output, size_t output_size,
                               uint64_t deadline_us) {
    if (!initialized_.load()) {
        return KernelStatus::ERROR_INIT;
    }
    
    if (!input || !output || input_size == 0 || output_size == 0) {
        return KernelStatus::ERROR_INVALID_INPUT;
    }
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    // Spike encoding: convert input to spike trains
    std::vector<float> spike_train(config_.num_neurons, 0.0f);
    
    // Simple rate encoding: higher input values = more spikes
    for (size_t i = 0; i < std::min(input_size, config_.num_neurons); ++i) {
        float rate = std::clamp(input[i], 0.0f, 1.0f);
        spike_train[i] = (rate > 0.5f) ? 1.0f : 0.0f;
    }
    
    // Process through SNN
    process_spike_train(spike_train.data(), spike_train.size());
    
    // Get field state as output
    size_t state_size = 0;
    std::vector<float> field_state(config_.field_size);
    field_manager_->get_state(field_state.data(), &state_size);
    
    // Map field state to output
    for (size_t i = 0; i < std::min(output_size, state_size); ++i) {
        output[i] = std::tanh(field_state[i]); // Normalize to [-1, 1]
    }
    
    // Update statistics
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(
        end_time - start_time).count();
    
    stats_.total_inferences++;
    stats_.avg_inference_time_us = 
        (stats_.avg_inference_time_us * (stats_.total_inferences - 1) + duration) 
        / stats_.total_inferences;
    
    // Check deadline
    if (deadline_us > 0 && static_cast<uint64_t>(duration) > deadline_us) {
        stats_.missed_deadlines++;
        return KernelStatus::ERROR_TIMEOUT;
    }
    
    return KernelStatus::OK;
}

KernelStatus SNNKernel::train(const float* data, size_t data_size,
                               const char* label, size_t label_size,
                               uint32_t epochs) {
    if (!initialized_.load()) {
        return KernelStatus::ERROR_INIT;
    }
    
    if (!data || data_size == 0) {
        return KernelStatus::ERROR_INVALID_INPUT;
    }
    
    // Training loop
    for (uint32_t epoch = 0; epoch < epochs; ++epoch) {
        // Convert data to spike patterns
        std::vector<float> delta(config_.field_size, 0.0f);
        
        for (size_t i = 0; i < std::min(data_size, config_.field_size); ++i) {
            delta[i] = data[i] * config_.learning_rate;
        }
        
        // Update field with gradient
        update_field(delta.data());
    }
    
    return KernelStatus::OK;
}

KernelStatus SNNKernel::get_field_state(float* state, size_t* state_size) const {
    if (!state || !state_size) {
        return KernelStatus::ERROR_INVALID_INPUT;
    }
    
    field_manager_->get_state(state, state_size);
    return KernelStatus::OK;
}

KernelStatus SNNKernel::set_field_state(const float* state, size_t state_size) {
    if (!state || state_size == 0) {
        return KernelStatus::ERROR_INVALID_INPUT;
    }
    
    field_manager_->set_state(state, state_size);
    return KernelStatus::OK;
}

SNNKernel::Stats SNNKernel::get_stats() const {
    std::lock_guard<std::mutex> lock(state_mutex_);
    auto stats = stats_;
    stats.field_variance = field_manager_->compute_variance();
    stats.syntropy_level = field_manager_->compute_resonance();
    return stats;
}

void SNNKernel::reset_stats() {
    std::lock_guard<std::mutex> lock(state_mutex_);
    stats_ = Stats{};
}

bool SNNKernel::is_stable() const {
    float variance = field_manager_->compute_variance();
    return variance < STABILITY_THRESHOLD;
}

float SNNKernel::get_field_resonance() const {
    return field_manager_->compute_resonance();
}

void SNNKernel::process_spike_train(const float* spikes, size_t num_spikes) {
    // Count total spikes
    size_t spike_count = 0;
    for (size_t i = 0; i < num_spikes; ++i) {
        if (spikes[i] > 0.5f) spike_count++;
    }
    
    stats_.total_spikes += spike_count;
    
    // Apply spike influence to field
    std::vector<float> field_delta(config_.field_size, 0.0f);
    
    for (size_t i = 0; i < std::min(num_spikes, config_.field_size); ++i) {
        if (spikes[i] > 0.5f) {
            field_delta[i] = config_.learning_rate;
        }
    }
    
    update_field(field_delta.data());
}

void SNNKernel::update_field(const float* delta) {
    field_manager_->update(delta, config_.field_size);
}

float SNNKernel::compute_resonance() const {
    return field_manager_->compute_resonance();
}

// ============================================================================
// FieldManager Implementation
// ============================================================================

FieldManager::FieldManager(size_t field_size) 
    : field_size_(field_size) {
    field_data_.resize(field_size, 0.0f);
    oscillation_phase_.resize(field_size, 0.0f);
    
    // Initialize phases
    for (size_t i = 0; i < field_size; ++i) {
        oscillation_phase_[i] = 2.0f * M_PI * i / field_size;
    }
}

FieldManager::~FieldManager() = default;

void FieldManager::update(const float* delta, size_t size) {
    std::lock_guard<std::mutex> lock(field_mutex_);
    
    size_t update_size = std::min(size, field_size_);
    
    for (size_t i = 0; i < update_size; ++i) {
        // Apply delta with oscillatory modulation
        float oscillation = std::sin(oscillation_phase_[i]);
        field_data_[i] += delta[i] * (1.0f + 0.1f * oscillation);
        
        // Update phase
        oscillation_phase_[i] += 0.1f;
        if (oscillation_phase_[i] > 2.0f * M_PI) {
            oscillation_phase_[i] -= 2.0f * M_PI;
        }
        
        // Clamp to prevent overflow
        field_data_[i] = std::clamp(field_data_[i], -10.0f, 10.0f);
    }
}

void FieldManager::get_state(float* output, size_t* size) const {
    std::lock_guard<std::mutex> lock(field_mutex_);
    
    if (output && size) {
        *size = field_size_;
        std::copy(field_data_.begin(), field_data_.end(), output);
    }
}

void FieldManager::set_state(const float* input, size_t size) {
    std::lock_guard<std::mutex> lock(field_mutex_);
    
    size_t copy_size = std::min(size, field_size_);
    std::copy(input, input + copy_size, field_data_.begin());
}

float FieldManager::compute_variance() const {
    std::lock_guard<std::mutex> lock(field_mutex_);
    
    float mean = 0.0f;
    for (const auto& val : field_data_) {
        mean += val;
    }
    mean /= field_size_;
    
    float variance = 0.0f;
    for (const auto& val : field_data_) {
        float diff = val - mean;
        variance += diff * diff;
    }
    
    return variance / field_size_;
}

float FieldManager::compute_resonance() const {
    std::lock_guard<std::mutex> lock(field_mutex_);
    
    // Compute coherence using correlation
    float resonance = 0.0f;
    
    for (size_t i = 0; i < field_size_ - 1; ++i) {
        float correlation = field_data_[i] * field_data_[i + 1];
        resonance += std::abs(correlation);
    }
    
    return resonance / (field_size_ - 1);
}

void FieldManager::apply_vibrational_mode(const float* mode, size_t size) {
    std::lock_guard<std::mutex> lock(field_mutex_);
    
    size_t apply_size = std::min(size, field_size_);
    
    for (size_t i = 0; i < apply_size; ++i) {
        field_data_[i] += mode[i] * 0.01f; // Small vibrational coupling
    }
}

// ============================================================================
// DroneKernelInterface Implementation
// ============================================================================

DroneKernelInterface::DroneKernelInterface(SNNKernel* kernel)
    : kernel_(kernel) {
    control_buffer_.fill(0.0f);
}

DroneKernelInterface::~DroneKernelInterface() = default;

KernelStatus DroneKernelInterface::process_control_cycle(
    const DroneState& state, ControlOutput& output) {
    
    // Prepare input vector from drone state
    std::vector<float> input(16);
    std::copy(state.position, state.position + 3, input.begin());
    std::copy(state.velocity, state.velocity + 3, input.begin() + 3);
    std::copy(state.orientation, state.orientation + 4, input.begin() + 6);
    std::copy(state.angular_vel, state.angular_vel + 3, input.begin() + 10);
    
    // Normalize inputs to [0, 1]
    for (auto& val : input) {
        val = std::tanh(val * 0.1f) * 0.5f + 0.5f;
    }
    
    // Run SNN inference with 1ms deadline
    std::vector<float> snn_output(4);
    auto status = kernel_->infer(input.data(), input.size(),
                                 snn_output.data(), snn_output.size(),
                                 1000); // 1ms deadline
    
    if (status != KernelStatus::OK) {
        // Fallback to safe defaults
        output.throttle = 0.5f;
        output.roll = 0.0f;
        output.pitch = 0.0f;
        output.yaw = 0.0f;
        output.emergency_stop = true;
        return status;
    }
    
    // Map SNN output to control signals
    output.throttle = std::clamp(snn_output[0], 0.0f, 1.0f);
    output.roll = std::clamp(snn_output[1], -1.0f, 1.0f);
    output.pitch = std::clamp(snn_output[2], -1.0f, 1.0f);
    output.yaw = std::clamp(snn_output[3], -1.0f, 1.0f);
    output.emergency_stop = false;
    
    return KernelStatus::OK;
}

KernelStatus DroneKernelInterface::fuse_sensor_data(
    const float* imu_data, size_t imu_size,
    const float* vision_data, size_t vision_size,
    DroneState& fused_state) {
    
    // Combine sensor data
    std::vector<float> combined(imu_size + vision_size);
    std::copy(imu_data, imu_data + imu_size, combined.begin());
    std::copy(vision_data, vision_data + vision_size, combined.begin() + imu_size);
    
    // Use SNN to fuse data
    std::vector<float> fusion_output(13); // 3 pos + 3 vel + 4 quat + 3 ang_vel
    auto status = kernel_->infer(combined.data(), combined.size(),
                                 fusion_output.data(), fusion_output.size());
    
    if (status != KernelStatus::OK) {
        return status;
    }
    
    // Map to fused state
    std::copy(fusion_output.begin(), fusion_output.begin() + 3, fused_state.position);
    std::copy(fusion_output.begin() + 3, fusion_output.begin() + 6, fused_state.velocity);
    std::copy(fusion_output.begin() + 6, fusion_output.begin() + 10, fused_state.orientation);
    std::copy(fusion_output.begin() + 10, fusion_output.begin() + 13, fused_state.angular_vel);
    
    fused_state.timestamp_us = std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    
    return KernelStatus::OK;
}

bool DroneKernelInterface::detect_collision_risk(
    const float* obstacle_data, size_t data_size, float& risk_score) {
    
    // Use SNN to assess collision risk
    float output = 0.0f;
    auto status = kernel_->infer(obstacle_data, data_size, &output, 1, 500); // 0.5ms deadline
    
    if (status != KernelStatus::OK) {
        risk_score = 1.0f; // Assume high risk on error
        return true;
    }
    
    risk_score = std::clamp(output, 0.0f, 1.0f);
    return risk_score > 0.7f; // Threshold for collision warning
}

void DroneKernelInterface::update_pid_gains(const DroneState& state) {
    // Adaptive PID tuning based on field resonance
    float resonance = kernel_->get_field_resonance();
    
    // Higher resonance = more aggressive control
    pid_state_.kp = 1.0f + resonance * 0.5f;
    pid_state_.ki = 0.1f + resonance * 0.05f;
    pid_state_.kd = 0.05f + resonance * 0.02f;
}

// ============================================================================
// RealtimeScheduler Implementation
// ============================================================================

RealtimeScheduler::RealtimeScheduler() = default;
RealtimeScheduler::~RealtimeScheduler() {
    stop();
}

bool RealtimeScheduler::schedule_task(ProcessPriority priority,
                                     std::function<void()> task,
                                     uint64_t deadline_us) {
    if (!task) return false;
    
    // Execute immediately for now (simple implementation)
    // Production version would use priority queue
    auto start = std::chrono::high_resolution_clock::now();
    
    task();
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(
        end - start).count();
    
    if (deadline_us > 0 && static_cast<uint64_t>(duration) > deadline_us) {
        missed_deadlines_++;
        return false;
    }
    
    return true;
}

void RealtimeScheduler::run() {
    running_.store(true);
}

void RealtimeScheduler::stop() {
    running_.store(false);
}

uint32_t RealtimeScheduler::get_missed_deadlines() const {
    return missed_deadlines_.load();
}

// ============================================================================
// KernelMemoryInterface Implementation
// ============================================================================

KernelMemoryInterface& KernelMemoryInterface::instance() {
    static KernelMemoryInterface instance;
    return instance;
}

KernelMemoryInterface::KernelMemoryInterface() {
    // Check for hardware acceleration support
    // This would interface with actual hardware in production
    hardware_accel_available_ = false;
}

KernelMemoryInterface::~KernelMemoryInterface() = default;

void KernelMemoryInterface::write_register(uint32_t offset, uint32_t value) {
    // Memory-mapped I/O write
    if (mmio_base_) {
        volatile uint32_t* reg = static_cast<volatile uint32_t*>(mmio_base_) + offset;
        *reg = value;
    }
}

uint32_t KernelMemoryInterface::read_register(uint32_t offset) {
    if (mmio_base_) {
        volatile uint32_t* reg = static_cast<volatile uint32_t*>(mmio_base_) + offset;
        return *reg;
    }
    return 0;
}

KernelStatus KernelMemoryInterface::dma_transfer(const void* src, void* dst, size_t size) {
    if (!src || !dst || size == 0) {
        return KernelStatus::ERROR_INVALID_INPUT;
    }
    
    // Simple memcpy for now; production would use DMA controller
    std::memcpy(dst, src, size);
    return KernelStatus::OK;
}

bool KernelMemoryInterface::has_snn_accelerator() const {
    return hardware_accel_available_;
}

KernelStatus KernelMemoryInterface::offload_inference(const float* input, size_t size,
                                                      float* output) {
    if (!hardware_accel_available_) {
        return KernelStatus::ERROR_INIT;
    }
    
    // Hardware offload would go here
    return KernelStatus::OK;
}

} // namespace quadra
