#include "quadra_supervisory_controller.hpp"
#include <algorithm>
#include <numeric>
#include <cmath>
#include <random>

namespace quadra {
namespace supervisory {

// ============================================================================
// FieldDynamicsProcessor Implementation (PRESERVED MECHANISMS)
// ============================================================================

FieldDynamicsProcessor::FieldDynamicsProcessor(size_t field_size)
    : field_size_(field_size)
    , noise_gen_(std::random_device{}()) {
    
    field_state_.resize(field_size, 0.0f);
    plasticity_traces_.resize(field_size, 0.0f);
    
    // Initialize with small random values
    std::normal_distribution<float> init_dist(0.0f, 0.1f);
    for (auto& val : field_state_) {
        val = init_dist(noise_gen_);
    }
}

void FieldDynamicsProcessor::update_field(const float* input, size_t input_size) {
    // Map input to field state (preserves original dynamics)
    size_t map_size = std::min(input_size, field_size_);
    
    for (size_t i = 0; i < map_size; ++i) {
        // Oscillatory dynamics (preserved from original)
        float phase = 2.0f * M_PI * i / field_size_;
        float oscillation = std::sin(phase + internal_excitation_);
        
        // Update with input modulation
        field_state_[i] += input[i] * (1.0f + 0.1f * oscillation);
        
        // Bounds to prevent overflow
        field_state_[i] = std::clamp(field_state_[i], -10.0f, 10.0f);
    }
    
    // Update internal excitation for rate control
    internal_excitation_ += compute_internal_rate();
    if (internal_excitation_ > 2.0f * M_PI) {
        internal_excitation_ -= 2.0f * M_PI;
    }
}

void FieldDynamicsProcessor::regulate_variance() {
    // PRESERVED: Feedback loop maintaining variance
    float current_variance = get_field_variance();
    float variance_error = target_variance_ - current_variance;
    
    // Apply feedback correction
    apply_variance_feedback();
    
    // Adjust field to maintain target variance
    if (std::abs(variance_error) > 0.001f) {
        float correction = variance_feedback_gain_ * variance_error;
        
        for (auto& val : field_state_) {
            val *= (1.0f + correction);
        }
    }
}

void FieldDynamicsProcessor::apply_plasticity(float reward) {
    // PRESERVED: Plasticity update mechanism
    update_plasticity_traces();
    
    // Hebbian-like plasticity with reward modulation
    for (size_t i = 0; i < field_size_; ++i) {
        // Plasticity rule: Δw = η * reward * trace
        float update = base_plasticity_rate_ * reward * plasticity_traces_[i];
        field_state_[i] += update;
        
        // Decay plasticity trace
        plasticity_traces_[i] *= 0.95f;
    }
}

void FieldDynamicsProcessor::inject_stress_test_noise(float intensity) {
    // PRESERVED: Noise injection as stress-testing (NOT exploration)
    std::normal_distribution<float> noise_dist(0.0f, intensity);
    
    for (auto& val : field_state_) {
        // Add stress-test noise to probe robustness
        val += noise_dist(noise_gen_);
        val = std::clamp(val, -10.0f, 10.0f);
    }
}

float FieldDynamicsProcessor::get_field_mean() const {
    float sum = std::accumulate(field_state_.begin(), field_state_.end(), 0.0f);
    return sum / field_size_;
}

float FieldDynamicsProcessor::get_field_variance() const {
    float mean = get_field_mean();
    float variance = 0.0f;
    
    for (const auto& val : field_state_) {
        float diff = val - mean;
        variance += diff * diff;
    }
    
    return variance / field_size_;
}

float FieldDynamicsProcessor::get_syntropy_level() const {
    // Compute order/coherence in field
    float coherence = 0.0f;
    
    for (size_t i = 0; i < field_size_ - 1; ++i) {
        float correlation = field_state_[i] * field_state_[i + 1];
        coherence += std::abs(correlation);
    }
    
    return coherence / (field_size_ - 1);
}

float FieldDynamicsProcessor::compute_adaptation_rate() const {
    // PRESERVED: Rate control based on internal state
    return compute_internal_rate();
}

bool FieldDynamicsProcessor::is_field_stable() const {
    float variance = get_field_variance();
    return variance < 0.1f;  // Stable if low variance
}

void FieldDynamicsProcessor::apply_variance_feedback() {
    // Internal helper for variance regulation
    float mean = get_field_mean();
    
    // Centering to regulate mean
    for (auto& val : field_state_) {
        val -= mean * 0.01f;
    }
}

void FieldDynamicsProcessor::update_plasticity_traces() {
    // Update traces based on field activity
    for (size_t i = 0; i < field_size_; ++i) {
        plasticity_traces_[i] = std::tanh(field_state_[i]);
    }
}

float FieldDynamicsProcessor::compute_internal_rate() const {
    // Rate control based on field energy
    float energy = 0.0f;
    for (const auto& val : field_state_) {
        energy += val * val;
    }
    
    return 0.01f * std::tanh(energy / field_size_);
}

// ============================================================================
// SupervisoryController Implementation
// ============================================================================

SupervisoryController::SupervisoryController(
    const SupervisoryConfig& config,
    flight::FlightController* flight_controller)
    : config_(config)
    , flight_controller_(flight_controller) {
    
    // Create field processor with preserved dynamics
    field_processor_ = std::make_unique<FieldDynamicsProcessor>(config.field_size);
    
    // Initialize adaptive parameters to defaults
    adaptive_params_ = AdaptiveParameters{};
    
    // Reserve history buffers
    state_history_.resize(100);
    performance_history_.resize(100);
}

SupervisoryController::~SupervisoryController() = default;

KernelStatus SupervisoryController::initialize() {
    // Initialize field processor
    std::vector<float> init_input(config_.field_size, 0.0f);
    field_processor_->update_field(init_input.data(), init_input.size());
    
    return KernelStatus::OK;
}

void SupervisoryController::update(const SupervisoryState& state) {
    auto start_time = std::chrono::steady_clock::now();
    
    current_state_ = state;
    
    // Update field state with drone-specific inputs
    current_state_.field_state = field_processor_->get_field_state();
    current_state_.field_mean = field_processor_->get_field_mean();
    current_state_.field_variance = field_processor_->get_field_variance();
    current_state_.syntropy_level = field_processor_->get_syntropy_level();
    
    // Construct extended field input
    auto field_input = construct_field_input(state);
    
    // Update field dynamics (PRESERVED)
    field_processor_->update_field(field_input.data(), field_input.size());
    
    // Variance regulation (PRESERVED)
    if (config_.maintain_variance_feedback) {
        field_processor_->regulate_variance();
    }
    
    // Stress-test noise injection (PRESERVED)
    if (config_.use_noise_injection_stress_test) {
        float noise_level = adaptive_params_.exploration.noise_injection_level;
        field_processor_->inject_stress_test_noise(noise_level);
    }
    
    // Compute reward for plasticity
    float reward = compute_reward();
    
    // Apply plasticity (PRESERVED)
    if (config_.enable_plasticity) {
        field_processor_->apply_plasticity(reward);
    }
    
    // Parameter adaptation (only if safe and enabled)
    if (config_.enable_adaptation && is_safe_to_adapt()) {
        adapt_gain_schedule(reward);
        adapt_control_envelope(state.stability_margin);
        adapt_mode_switching(state.tracking_error);
        adapt_exploration_params(stats_.adaptation_confidence);
    }
    
    // Enforce safety bounds
    enforce_parameter_bounds();
    
    // Apply to flight controller
    apply_parameters_to_controller();
    
    // Update statistics
    stats_.total_updates++;
    auto end_time = std::chrono::steady_clock::now();
    auto duration_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        end_time - start_time).count();
    
    stats_.avg_update_time_ms = 
        (stats_.avg_update_time_ms * (stats_.total_updates - 1) + duration_ms) 
        / stats_.total_updates;
    
    stats_.field_stability = field_processor_->is_field_stable() ? 1.0f : 0.0f;
    
    // Store history
    state_history_.push_back(current_state_);
    if (state_history_.size() > 100) {
        state_history_.pop_front();
    }
    
    performance_history_.push_back(reward);
    if (performance_history_.size() > 100) {
        performance_history_.pop_front();
    }
}

std::vector<float> SupervisoryController::construct_field_input(
    const SupervisoryState& state) {
    
    std::vector<float> input(config_.field_size, 0.0f);
    
    size_t idx = 0;
    
    // IMU residuals (added to field)
    if (idx + 3 <= input.size()) {
        input[idx++] = state.imu_residuals[0];
        input[idx++] = state.imu_residuals[1];
        input[idx++] = state.imu_residuals[2];
    }
    
    // Wind estimation error (added to field)
    if (idx + 3 <= input.size()) {
        input[idx++] = state.wind_estimate_error[0];
        input[idx++] = state.wind_estimate_error[1];
        input[idx++] = state.wind_estimate_error[2];
    }
    
    // Control effort variance (added to field)
    if (idx < input.size()) {
        input[idx++] = state.control_effort_variance;
    }
    
    // State estimator uncertainty (added to field)
    if (idx < input.size()) {
        input[idx++] = state.state_estimator_uncertainty;
    }
    
    // Performance metrics
    if (idx + 3 <= input.size()) {
        input[idx++] = state.tracking_error;
        input[idx++] = state.stability_margin;
        input[idx++] = state.disturbance_rejection;
    }
    
    // Normalize inputs
    for (auto& val : input) {
        val = std::tanh(val * 0.1f);
    }
    
    return input;
}

void SupervisoryController::adapt_gain_schedule(float reward) {
    // Adjust gain schedules based on performance
    float adaptation_rate = config_.learning_rate * 
                          field_processor_->compute_adaptation_rate();
    
    // Increase gains if performance is good
    if (reward > 0.5f && field_processor_->is_field_stable()) {
        adaptive_params_.gain_schedule.position_kp_scale += adaptation_rate * 0.1f;
        adaptive_params_.gain_schedule.attitude_kp_scale += adaptation_rate * 0.1f;
        stats_.parameter_changes++;
    }
    // Decrease gains if unstable
    else if (reward < 0.3f) {
        adaptive_params_.gain_schedule.position_kp_scale -= adaptation_rate * 0.05f;
        adaptive_params_.gain_schedule.attitude_kp_scale -= adaptation_rate * 0.05f;
        stats_.parameter_changes++;
    }
}

void SupervisoryController::adapt_control_envelope(float safety_margin) {
    // Adjust control envelope based on safety margin
    float adaptation_rate = config_.learning_rate;
    
    if (safety_margin > 0.8f && field_processor_->is_field_stable()) {
        // Can expand envelope slightly
        adaptive_params_.control_envelope.max_tilt_angle_deg += adaptation_rate * 0.5f;
        adaptive_params_.control_envelope.max_horizontal_speed += adaptation_rate * 0.1f;
        stats_.parameter_changes++;
    } else if (safety_margin < 0.4f) {
        // Contract envelope for safety
        adaptive_params_.control_envelope.max_tilt_angle_deg -= adaptation_rate * 1.0f;
        adaptive_params_.control_envelope.max_horizontal_speed -= adaptation_rate * 0.2f;
        stats_.parameter_changes++;
    }
}

void SupervisoryController::adapt_mode_switching(float performance_metric) {
    // Adjust mode switching thresholds
    float adaptation_rate = config_.learning_rate * 0.5f;
    
    // Adapt GPS vs vision weight based on performance
    if (current_state_.state_estimator_uncertainty > 0.5f) {
        // High uncertainty - rely more on GPS
        adaptive_params_.mode_switching.gps_weight_schedule += adaptation_rate * 0.1f;
        stats_.parameter_changes++;
    } else if (current_state_.state_estimator_uncertainty < 0.2f) {
        // Low uncertainty - can use more vision
        adaptive_params_.mode_switching.gps_weight_schedule -= adaptation_rate * 0.05f;
        stats_.parameter_changes++;
    }
}

void SupervisoryController::adapt_exploration_params(float confidence) {
    // Adjust exploration vs exploitation
    float adaptation_rate = config_.learning_rate * 0.1f;
    
    // High confidence - reduce exploration
    if (confidence > 0.7f) {
        adaptive_params_.exploration.exploration_rate -= adaptation_rate * 0.01f;
        adaptive_params_.exploration.noise_injection_level -= adaptation_rate * 0.005f;
    }
    // Low confidence - increase exploration
    else if (confidence < 0.4f) {
        adaptive_params_.exploration.exploration_rate += adaptation_rate * 0.02f;
        adaptive_params_.exploration.noise_injection_level += adaptation_rate * 0.01f;
    }
    
    // Update confidence estimate
    float stability = field_processor_->is_field_stable() ? 1.0f : 0.0f;
    float performance_avg = performance_history_.empty() ? 0.5f :
        std::accumulate(performance_history_.begin(), performance_history_.end(), 0.0f) 
        / performance_history_.size();
    
    stats_.adaptation_confidence = 0.7f * stability + 0.3f * performance_avg;
}

bool SupervisoryController::is_safe_to_adapt() const {
    // Safety checks before adapting
    
    // Check certification mode
    if (config_.cert_mode == flight::CertificationMode::CERTIFIED ||
        config_.cert_mode == flight::CertificationMode::FLIGHT_CRITICAL) {
        return false;  // No adaptation in certified modes
    }
    
    // Check field stability requirement
    if (config_.require_stability_for_adaptation) {
        if (!field_processor_->is_field_stable()) {
            return false;
        }
        
        if (stats_.field_stability < config_.min_stability_threshold) {
            return false;
        }
    }
    
    return true;
}

void SupervisoryController::enforce_parameter_bounds() {
    // Enforce safety bounds on all parameters
    
    // Gain schedule bounds
    auto& gs = adaptive_params_.gain_schedule;
    gs.position_kp_scale = std::clamp(gs.position_kp_scale, 
        AdaptiveParameters::MIN_GAIN_SCALE, AdaptiveParameters::MAX_GAIN_SCALE);
    gs.attitude_kp_scale = std::clamp(gs.attitude_kp_scale,
        AdaptiveParameters::MIN_GAIN_SCALE, AdaptiveParameters::MAX_GAIN_SCALE);
    gs.altitude_kp_scale = std::clamp(gs.altitude_kp_scale,
        AdaptiveParameters::MIN_GAIN_SCALE, AdaptiveParameters::MAX_GAIN_SCALE);
    gs.derivative_gain_scale = std::clamp(gs.derivative_gain_scale,
        AdaptiveParameters::MIN_GAIN_SCALE, AdaptiveParameters::MAX_GAIN_SCALE);
    gs.integral_limit_scale = std::clamp(gs.integral_limit_scale,
        0.5f, 2.0f);
    
    // Control envelope bounds
    auto& ce = adaptive_params_.control_envelope;
    ce.max_tilt_angle_deg = std::clamp(ce.max_tilt_angle_deg, 15.0f, 45.0f);
    ce.max_vertical_speed = std::clamp(ce.max_vertical_speed, 2.0f, 10.0f);
    ce.max_horizontal_speed = std::clamp(ce.max_horizontal_speed, 5.0f, 20.0f);
    ce.max_yaw_rate = std::clamp(ce.max_yaw_rate, 45.0f, 180.0f);
    
    // Mode switching bounds
    auto& ms = adaptive_params_.mode_switching;
    ms.aggressive_mode_threshold = std::clamp(ms.aggressive_mode_threshold, 0.6f, 0.95f);
    ms.conservative_mode_threshold = std::clamp(ms.conservative_mode_threshold, 0.1f, 0.5f);
    ms.gps_weight_schedule = std::clamp(ms.gps_weight_schedule, 0.3f, 0.95f);
    ms.position_hold_tolerance = std::clamp(ms.position_hold_tolerance, 0.1f, 2.0f);
    
    // Exploration bounds
    auto& ex = adaptive_params_.exploration;
    ex.exploration_rate = std::clamp(ex.exploration_rate, 0.0f, 0.3f);
    ex.noise_injection_level = std::clamp(ex.noise_injection_level, 0.0f, 0.2f);
    ex.adaptation_rate = std::clamp(ex.adaptation_rate, 0.001f, 0.05f);
    ex.confidence_threshold = std::clamp(ex.confidence_threshold, 0.5f, 0.9f);
}

float SupervisoryController::compute_reward() const {
    // Compute reward signal for plasticity
    float tracking_penalty = std::exp(-current_state_.tracking_error);
    float stability_reward = current_state_.stability_margin;
    float disturbance_reward = current_state_.disturbance_rejection;
    
    // Combined reward
    float reward = 0.5f * tracking_penalty + 
                  0.3f * stability_reward + 
                  0.2f * disturbance_reward;
    
    return std::clamp(reward, 0.0f, 1.0f);
}

void SupervisoryController::apply_parameters_to_controller() {
    // This would apply parameters to the flight controller
    // Implementation depends on flight controller API
    // NOTE: NEVER directly commands motors - only adjusts parameters
}

SupervisoryState SupervisoryController::get_current_state() const {
    return current_state_;
}

SupervisoryController::Statistics SupervisoryController::get_statistics() const {
    return stats_;
}

void SupervisoryController::enable_adaptation(bool enable) {
    config_.enable_adaptation = enable;
}

void SupervisoryController::reset_to_defaults() {
    adaptive_params_ = AdaptiveParameters{};
    stats_ = Statistics{};
}

// ============================================================================
// SupervisoryIntegration Implementation
// ============================================================================

SupervisoryIntegration::SupervisoryIntegration(
    flight::FlightController* flight_controller,
    const SupervisoryConfig& config)
    : flight_controller_(flight_controller) {
    
    supervisor_ = std::make_unique<SupervisoryController>(config, flight_controller);
    update_period_ms_ = 1000 / config.update_frequency_hz;
}

SupervisoryIntegration::~SupervisoryIntegration() {
    stop();
}

void SupervisoryIntegration::fast_control_callback(
    const flight::DroneKernelInterface::DroneState& state,
    const flight::DroneKernelInterface::ControlOutput& output) {
    
    // Accumulate data from fast control loop
    accumulate_state_data(state, output);
}

void SupervisoryIntegration::run_supervisory_thread() {
    while (running_.load()) {
        auto now = std::chrono::steady_clock::now();
        
        // Build supervisory state from accumulated data
        SupervisoryState sup_state = build_supervisory_state();
        
        // Run supervisory update (slow, 5-20 Hz)
        supervisor_->update(sup_state);
        
        // Sleep until next update
        auto next_update = now + std::chrono::milliseconds(update_period_ms_);
        std::this_thread::sleep_until(next_update);
    }
}

void SupervisoryIntegration::start() {
    supervisor_->initialize();
    running_.store(true);
    supervisory_thread_ = std::thread(&SupervisoryIntegration::run_supervisory_thread, this);
}

void SupervisoryIntegration::stop() {
    running_.store(false);
    if (supervisory_thread_.joinable()) {
        supervisory_thread_.join();
    }
}

SupervisoryState SupervisoryIntegration::build_supervisory_state() {
    std::lock_guard<std::mutex> lock(state_mutex_);
    
    SupervisoryState state{};
    state.timestamp_us = std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
    
    // Compute IMU residuals from accumulated errors
    if (!accumulated_.imu_errors.empty()) {
        for (const auto& err : accumulated_.imu_errors) {
            state.imu_residuals[0] += err[0];
            state.imu_residuals[1] += err[1];
            state.imu_residuals[2] += err[2];
        }
        float count = static_cast<float>(accumulated_.imu_errors.size());
        state.imu_residuals[0] /= count;
        state.imu_residuals[1] /= count;
        state.imu_residuals[2] /= count;
    }
    
    // Wind estimation error
    state.wind_estimate_error[0] = accumulated_.wind_x_estimate;
    state.wind_estimate_error[1] = accumulated_.wind_y_estimate;
    state.wind_estimate_error[2] = accumulated_.wind_z_estimate;
    
    // Control effort variance
    if (!accumulated_.control_efforts.empty()) {
        float mean = std::accumulate(accumulated_.control_efforts.begin(),
                                    accumulated_.control_efforts.end(), 0.0f) 
                    / accumulated_.control_efforts.size();
        float variance = 0.0f;
        for (float effort : accumulated_.control_efforts) {
            float diff = effort - mean;
            variance += diff * diff;
        }
        state.control_effort_variance = variance / accumulated_.control_efforts.size();
    }
    
    // Clear accumulated data
    accumulated_ = AccumulatedState{};
    
    return state;
}

void SupervisoryIntegration::accumulate_state_data(
    const flight::DroneKernelInterface::DroneState& state,
    const flight::DroneKernelInterface::ControlOutput& output) {
    
    std::lock_guard<std::mutex> lock(state_mutex_);
    
    // Accumulate IMU errors (simplified - would use actual estimator residuals)
    std::array<float, 3> imu_err = {
        state.velocity[0] * 0.01f,
        state.velocity[1] * 0.01f,
        state.velocity[2] * 0.01f
    };
    accumulated_.imu_errors.push_back(imu_err);
    
    // Accumulate control effort
    float effort = std::abs(output.roll) + std::abs(output.pitch) + 
                  std::abs(output.yaw) + std::abs(output.throttle - 0.5f);
    accumulated_.control_efforts.push_back(effort);
    
    // Simple wind estimation (would use proper estimator)
    accumulated_.wind_x_estimate = state.velocity[0] * 0.05f;
    accumulated_.wind_y_estimate = state.velocity[1] * 0.05f;
    
    // Limit buffer sizes
    if (accumulated_.imu_errors.size() > 1000) {
        accumulated_.imu_errors.erase(accumulated_.imu_errors.begin());
    }
    if (accumulated_.control_efforts.size() > 1000) {
        accumulated_.control_efforts.erase(accumulated_.control_efforts.begin());
    }
}

} // namespace supervisory
} // namespace quadra
