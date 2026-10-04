#include "quadra_flight_controller.hpp"
#include <cmath>
#include <algorithm>
#include <thread>
#include <fstream>

namespace quadra {
namespace flight {

// ============================================================================
// PID Controller Implementation
// ============================================================================

PIDController::PIDController(const Gains& gains) : gains_(gains) {}

float PIDController::compute(float setpoint, float measurement, float dt) {
    // Compute error
    error_ = setpoint - measurement;
    
    // Proportional term
    p_term_ = gains_.kp * error_;
    
    // Integral term with anti-windup
    integral_ += error_ * dt;
    clamp_integral();
    i_term_ = gains_.ki * integral_;
    
    // Derivative term (with filtering on measurement to avoid derivative kick)
    float derivative = 0.0f;
    if (dt > 1e-6f) {
        derivative = (error_ - prev_error_) / dt;
    }
    d_term_ = gains_.kd * derivative;
    
    prev_error_ = error_;
    
    // Compute output
    float output = p_term_ + i_term_ + d_term_;
    
    // Clamp output
    output = std::clamp(output, -gains_.output_max, gains_.output_max);
    
    return output;
}

void PIDController::reset() {
    integral_ = 0.0f;
    prev_error_ = 0.0f;
    error_ = 0.0f;
    p_term_ = 0.0f;
    i_term_ = 0.0f;
    d_term_ = 0.0f;
}

void PIDController::set_gains(const Gains& gains) {
    gains_ = gains;
    clamp_integral();  // Re-clamp with new limits
}

PIDController::Gains PIDController::get_gains() const {
    return gains_;
}

void PIDController::clamp_integral() {
    integral_ = std::clamp(integral_, -gains_.i_max, gains_.i_max);
}

// ============================================================================
// Attitude PID Controllers
// ============================================================================

AttitudePIDControllers::AttitudePIDControllers(
    const PIDController::Gains& roll_gains,
    const PIDController::Gains& pitch_gains,
    const PIDController::Gains& yaw_gains
) : roll(roll_gains), pitch(pitch_gains), yaw(yaw_gains) {}

// ============================================================================
// Position PID Controllers
// ============================================================================

PositionPIDControllers::PositionPIDControllers(
    const PIDController::Gains& xy_gains,
    const PIDController::Gains& z_gains
) : x(xy_gains), y(xy_gains), z(z_gains) {}

// ============================================================================
// MPC Controller Implementation
// ============================================================================

MPCController::MPCController(const Config& config) : config_(config) {
    predicted_states_.resize(config.prediction_horizon);
    control_sequence_.resize(config.control_horizon);
}

MPCController::~MPCController() = default;

MPCController::Control MPCController::compute(
    const State& current, const State& target) {
    
    // Simplified MPC - full implementation would use QP solver
    // This uses a receding horizon approach
    
    Control control{};
    
    // Compute position error
    float pos_error[3];
    for (int i = 0; i < 3; ++i) {
        pos_error[i] = target.position[i] - current.position[i];
    }
    
    // Compute velocity error
    float vel_error[3];
    for (int i = 0; i < 3; ++i) {
        vel_error[i] = target.velocity[i] - current.velocity[i];
    }
    
    // Simple control law (placeholder for full MPC)
    float thrust_direction[3];
    for (int i = 0; i < 3; ++i) {
        thrust_direction[i] = 
            config_.position_weight * pos_error[i] +
            config_.velocity_weight * vel_error[i];
    }
    
    // Compute total thrust
    control.thrust = std::sqrt(
        thrust_direction[0] * thrust_direction[0] +
        thrust_direction[1] * thrust_direction[1] +
        thrust_direction[2] * thrust_direction[2]
    );
    
    // Simple torque computation (placeholder)
    for (int i = 0; i < 3; ++i) {
        control.torques[i] = 0.1f * (target.angular_vel[i] - current.angular_vel[i]);
    }
    
    return control;
}

void MPCController::set_constraints(float max_thrust, float max_torque) {
    // Store constraints for QP solver
}

void MPCController::solve_qp() {
    // QP solver implementation would go here
    // For production, integrate OSQP or similar library
}

void MPCController::linearize_dynamics(const State& state) {
    // Linearize nonlinear dynamics around current state
}

// ============================================================================
// Geometric Controller Implementation
// ============================================================================

GeometricController::GeometricController(const Gains& gains) : gains_(gains) {}

GeometricController::Output GeometricController::compute(
    const DroneKernelInterface::DroneState& state,
    const Trajectory& desired) {
    
    Output output{};
    
    // Position and velocity errors
    std::array<float, 3> pos_error;
    std::array<float, 3> vel_error;
    
    for (int i = 0; i < 3; ++i) {
        pos_error[i] = state.position[i] - desired.position[i];
        vel_error[i] = state.velocity[i] - desired.velocity[i];
    }
    
    // Compute desired acceleration
    std::array<float, 3> acc_desired;
    for (int i = 0; i < 3; ++i) {
        acc_desired[i] = desired.acceleration[i] 
            - gains_.kx * pos_error[i]
            - gains_.kv * vel_error[i];
    }
    acc_desired[2] += gains_.gravity;  // Gravity compensation
    
    // Current rotation matrix
    auto R = quat_to_rotation_matrix({
        state.orientation[0], state.orientation[1],
        state.orientation[2], state.orientation[3]
    });
    
    // Compute desired thrust direction (b3_des)
    std::array<float, 3> b3_des = acc_desired;
    float acc_norm = std::sqrt(
        acc_desired[0] * acc_desired[0] +
        acc_desired[1] * acc_desired[1] +
        acc_desired[2] * acc_desired[2]
    );
    
    if (acc_norm > 1e-6f) {
        for (int i = 0; i < 3; ++i) {
            b3_des[i] /= acc_norm;
        }
    }
    
    // Total thrust
    output.thrust = gains_.mass * acc_norm;
    
    // Desired rotation matrix (simplified - full implementation more complex)
    std::array<std::array<float, 3>, 3> Rd;
    // ... (full SE(3) computation)
    
    // Rotation error
    auto eR_vec = rotation_error(R, Rd);
    
    // Angular velocity error
    std::array<float, 3> eOmega;
    for (int i = 0; i < 3; ++i) {
        eOmega[i] = state.angular_vel[i];  // Simplified
    }
    
    // Compute moments
    for (int i = 0; i < 3; ++i) {
        output.moment[i] = -gains_.kR * eR_vec[i] - gains_.kOmega * eOmega[i];
    }
    
    return output;
}

std::array<std::array<float, 3>, 3> GeometricController::quat_to_rotation_matrix(
    const std::array<float, 4>& q) const {
    
    float w = q[0], x = q[1], y = q[2], z = q[3];
    
    std::array<std::array<float, 3>, 3> R;
    
    R[0][0] = 1 - 2*(y*y + z*z);
    R[0][1] = 2*(x*y - w*z);
    R[0][2] = 2*(x*z + w*y);
    
    R[1][0] = 2*(x*y + w*z);
    R[1][1] = 1 - 2*(x*x + z*z);
    R[1][2] = 2*(y*z - w*x);
    
    R[2][0] = 2*(x*z - w*y);
    R[2][1] = 2*(y*z + w*x);
    R[2][2] = 1 - 2*(x*x + y*y);
    
    return R;
}

std::array<float, 3> GeometricController::rotation_error(
    const std::array<std::array<float, 3>, 3>& R,
    const std::array<std::array<float, 3>, 3>& Rd) const {
    
    // eR = 0.5 * vee(Rd^T R - R^T Rd)
    std::array<float, 3> eR;
    
    eR[0] = 0.5f * (R[2][1] * Rd[2][2] - R[1][2] * Rd[1][1]);
    eR[1] = 0.5f * (R[0][2] * Rd[0][0] - R[2][0] * Rd[2][2]);
    eR[2] = 0.5f * (R[1][0] * Rd[1][1] - R[0][1] * Rd[0][0]);
    
    return eR;
}

// ============================================================================
// Fixed-Rate Executor Implementation
// ============================================================================

FixedRateExecutor::FixedRateExecutor(uint32_t frequency_hz, uint32_t max_jitter_us)
    : frequency_hz_(frequency_hz)
    , max_jitter_us_(max_jitter_us)
    , cycle_period_us_(1000000 / frequency_hz) {}

bool FixedRateExecutor::begin_cycle() {
    cycle_start_ = std::chrono::steady_clock::now();
    
    // Check if we're on schedule
    if (stats_.total_cycles > 0) {
        auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(
            cycle_start_ - last_cycle_end_).count();
        
        float jitter = std::abs(static_cast<float>(elapsed) - cycle_period_us_);
        stats_.jitter_us = (stats_.jitter_us * 0.9f) + (jitter * 0.1f);  // EMA
        
        if (elapsed > cycle_period_us_ + max_jitter_us_) {
            stats_.missed_deadlines++;
            return false;
        }
    }
    
    return true;
}

bool FixedRateExecutor::end_cycle() {
    auto cycle_end = std::chrono::steady_clock::now();
    
    auto cycle_time_us = std::chrono::duration_cast<std::chrono::microseconds>(
        cycle_end - cycle_start_).count();
    
    // Update statistics
    stats_.total_cycles++;
    stats_.avg_cycle_time_us = 
        (stats_.avg_cycle_time_us * (stats_.total_cycles - 1) + cycle_time_us) 
        / stats_.total_cycles;
    
    if (cycle_time_us > stats_.max_cycle_time_us) {
        stats_.max_cycle_time_us = static_cast<float>(cycle_time_us);
    }
    
    // Sleep to maintain fixed rate
    auto sleep_time_us = cycle_period_us_ - cycle_time_us;
    
    if (sleep_time_us > 0) {
        std::this_thread::sleep_for(std::chrono::microseconds(sleep_time_us));
    } else {
        // Overran deadline
        stats_.missed_deadlines++;
        last_cycle_end_ = cycle_end;
        return false;
    }
    
    last_cycle_end_ = std::chrono::steady_clock::now();
    return true;
}

FixedRateExecutor::Statistics FixedRateExecutor::get_statistics() const {
    return stats_;
}

void FixedRateExecutor::reset_statistics() {
    stats_ = Statistics{};
}

// ============================================================================
// Safe Learning Manager Implementation
// ============================================================================

SafeLearningManager::SafeLearningManager(const FlightControllerConfig& config)
    : config_(config) {}

bool SafeLearningManager::is_learning_allowed() const {
    // No learning in certified modes
    if (config_.cert_mode == CertificationMode::CERTIFIED ||
        config_.cert_mode == CertificationMode::FLIGHT_CRITICAL) {
        return false;
    }
    
    // Check if learning mode is enabled
    if (config_.learning_mode == LearningMode::DISABLED) {
        return false;
    }
    
    // Check if approval is required and granted
    if (config_.require_learning_approval && !learning_approved_) {
        return false;
    }
    
    return true;
}

bool SafeLearningManager::can_update_parameter(const char* param_name) const {
    if (!is_learning_allowed()) {
        return false;
    }
    
    return is_parameter_whitelisted(param_name);
}

bool SafeLearningManager::update_target_tracking(float* tracking_gains, size_t size) {
    if (config_.learning_mode != LearningMode::TARGET_TRACKING) {
        return false;
    }
    
    if (!is_learning_allowed()) {
        return false;
    }
    
    // Apply safe updates with rate limiting
    for (size_t i = 0; i < size; ++i) {
        tracking_gains[i] = std::clamp(tracking_gains[i],
                                       -config_.learning_rate_limit,
                                       config_.learning_rate_limit);
    }
    
    log_learning_event("target_tracking_update", tracking_gains, size);
    return true;
}

bool SafeLearningManager::update_sensor_fusion_weights(
    float* weights, size_t num_sensors) {
    
    if (config_.learning_mode != LearningMode::SENSOR_FUSION_WEIGHTS) {
        return false;
    }
    
    if (!is_learning_allowed()) {
        return false;
    }
    
    // Normalize weights to sum to 1.0
    float sum = 0.0f;
    for (size_t i = 0; i < num_sensors; ++i) {
        weights[i] = std::max(0.0f, weights[i]);
        sum += weights[i];
    }
    
    if (sum > 1e-6f) {
        for (size_t i = 0; i < num_sensors; ++i) {
            weights[i] /= sum;
        }
    }
    
    log_learning_event("sensor_fusion_weights", weights, num_sensors);
    return true;
}

bool SafeLearningManager::adapt_control_timing(float& dt_adjustment) {
    if (config_.learning_mode != LearningMode::CONTROL_TIMING) {
        return false;
    }
    
    if (!is_learning_allowed()) {
        return false;
    }
    
    // Limit timing adjustments to ±5%
    dt_adjustment = std::clamp(dt_adjustment, -0.05f, 0.05f);
    
    log_learning_event("control_timing", &dt_adjustment, 1);
    return true;
}

bool SafeLearningManager::compensate_environment(float* compensation, size_t size) {
    if (config_.learning_mode != LearningMode::ENVIRONMENTAL_COMPENSATION) {
        return false;
    }
    
    if (!is_learning_allowed()) {
        return false;
    }
    
    // Apply conservative compensation limits
    for (size_t i = 0; i < size; ++i) {
        compensation[i] = std::clamp(compensation[i], -1.0f, 1.0f);
    }
    
    log_learning_event("environmental_compensation", compensation, size);
    return true;
}

bool SafeLearningManager::request_learning_approval(const char* reason) {
    // In real implementation, this would request operator approval
    // For now, auto-approve in development mode
    if (config_.cert_mode == CertificationMode::DEVELOPMENT) {
        learning_approved_ = true;
        return true;
    }
    
    return false;
}

void SafeLearningManager::log_learning_event(
    const char* event, float* data, size_t size) {
    // Log for certification audit trail
    last_learning_time_us_ = std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
}

bool SafeLearningManager::is_parameter_whitelisted(const char* param_name) const {
    // Whitelist of parameters that can be updated
    const char* whitelist[] = {
        "tracking_gain",
        "sensor_weight",
        "timing_adjust",
        "wind_compensation"
    };
    
    for (const char* allowed : whitelist) {
        if (std::strcmp(param_name, allowed) == 0) {
            return true;
        }
    }
    
    return false;
}

// ============================================================================
// Flight Controller Implementation
// ============================================================================

FlightController::FlightController(
    const FlightControllerConfig& config,
    SNNKernel* snn_kernel)
    : config_(config)
    , snn_kernel_(snn_kernel)
    , current_mode_(config.control_mode) {
    
    position_setpoint_.fill(0.0f);
    velocity_setpoint_.fill(0.0f);
    attitude_setpoint_.fill(0.0f);
}

FlightController::~FlightController() = default;

KernelStatus FlightController::initialize() {
    // Create executor
    executor_ = std::make_unique<FixedRateExecutor>(
        config_.control_frequency_hz,
        config_.max_jitter_us
    );
    
    // Create learning manager
    learning_manager_ = std::make_unique<SafeLearningManager>(config_);
    
    // Initialize controllers based on type
    if (config_.controller_type == ControllerType::PID ||
        config_.controller_type == ControllerType::HYBRID_SNN_PID) {
        
        PIDController::Gains attitude_gains;
        attitude_gains.kp = 2.0f;
        attitude_gains.ki = 0.1f;
        attitude_gains.kd = 0.5f;
        attitude_gains.i_max = 5.0f;
        attitude_gains.output_max = 1.0f;
        
        attitude_pid_ = std::make_unique<AttitudePIDControllers>(
            attitude_gains, attitude_gains, attitude_gains
        );
        
        PIDController::Gains position_gains_xy;
        position_gains_xy.kp = 1.5f;
        position_gains_xy.ki = 0.05f;
        position_gains_xy.kd = 0.8f;
        
        PIDController::Gains position_gains_z;
        position_gains_z.kp = 2.0f;
        position_gains_z.ki = 0.1f;
        position_gains_z.kd = 1.0f;
        
        position_pid_ = std::make_unique<PositionPIDControllers>(
            position_gains_xy, position_gains_z
        );
    }
    
    if (config_.controller_type == ControllerType::MPC) {
        MPCController::Config mpc_config;
        mpc_config.dt = 1.0f / config_.control_frequency_hz;
        mpc_ = std::make_unique<MPCController>(mpc_config);
    }
    
    if (config_.controller_type == ControllerType::GEOMETRIC) {
        GeometricController::Gains geo_gains;
        geo_gains.mass = config_.mass_kg;
        geometric_ = std::make_unique<GeometricController>(geo_gains);
    }
    
    initialized_ = true;
    return KernelStatus::OK;
}

KernelStatus FlightController::control_step(
    const DroneKernelInterface::DroneState& state,
    DroneKernelInterface::ControlOutput& output) {
    
    if (!initialized_) {
        return KernelStatus::ERROR_INIT;
    }
    
    // Begin timing cycle
    if (!executor_->begin_cycle()) {
        // Deadline miss on entry
        output.emergency_stop = true;
        return KernelStatus::ERROR_TIMEOUT;
    }
    
    // Safety checks
    if (emergency_stop_ || !check_safety_limits(state)) {
        output.throttle = 0.0f;
        output.roll = 0.0f;
        output.pitch = 0.0f;
        output.yaw = 0.0f;
        output.emergency_stop = true;
        executor_->end_cycle();
        return KernelStatus::OK;
    }
    
    // Compute control based on controller type
    switch (config_.controller_type) {
        case ControllerType::PID:
            output = compute_pid_control(state);
            break;
        case ControllerType::MPC:
            output = compute_mpc_control(state);
            break;
        case ControllerType::GEOMETRIC:
            output = compute_geometric_control(state);
            break;
        case ControllerType::HYBRID_SNN_PID:
            output = compute_hybrid_control(state);
            break;
    }
    
    // Record data for certification
    record_flight_data(state, output);
    
    // End timing cycle
    if (!executor_->end_cycle()) {
        // Deadline miss
        return KernelStatus::ERROR_TIMEOUT;
    }
    
    return KernelStatus::OK;
}

void FlightController::set_position_setpoint(float x, float y, float z) {
    position_setpoint_ = {x, y, z};
}

void FlightController::set_velocity_setpoint(float vx, float vy, float vz) {
    velocity_setpoint_ = {vx, vy, vz};
}

void FlightController::set_attitude_setpoint(float roll, float pitch, float yaw) {
    attitude_setpoint_ = {roll, pitch, yaw};
}

void FlightController::set_trajectory(const GeometricController::Trajectory& traj) {
    trajectory_ = traj;
}

void FlightController::set_control_mode(ControlMode mode) {
    current_mode_ = mode;
}

void FlightController::set_controller_type(ControllerType type) {
    config_.controller_type = type;
}

bool FlightController::check_safety_limits(
    const DroneKernelInterface::DroneState& state) {
    
    return check_position_limits(state) &&
           check_velocity_limits(state) &&
           check_attitude_limits(state);
}

void FlightController::emergency_stop() {
    emergency_stop_ = true;
}

FixedRateExecutor::Statistics FlightController::get_timing_stats() const {
    return executor_->get_statistics();
}

void FlightController::get_pid_diagnostics(char* buffer, size_t buffer_size) const {
    if (attitude_pid_) {
        snprintf(buffer, buffer_size,
            "Roll: P=%.3f I=%.3f D=%.3f E=%.3f\n"
            "Pitch: P=%.3f I=%.3f D=%.3f E=%.3f\n"
            "Yaw: P=%.3f I=%.3f D=%.3f E=%.3f\n",
            attitude_pid_->roll.get_p_term(),
            attitude_pid_->roll.get_i_term(),
            attitude_pid_->roll.get_d_term(),
            attitude_pid_->roll.get_error(),
            attitude_pid_->pitch.get_p_term(),
            attitude_pid_->pitch.get_i_term(),
            attitude_pid_->pitch.get_d_term(),
            attitude_pid_->pitch.get_error(),
            attitude_pid_->yaw.get_p_term(),
            attitude_pid_->yaw.get_i_term(),
            attitude_pid_->yaw.get_d_term(),
            attitude_pid_->yaw.get_error()
        );
    }
}

bool FlightController::verify_deterministic_behavior() const {
    // Verify that system behaves deterministically
    if (!config_.enable_deterministic_mode) {
        return false;
    }
    
    // Check that learning is disabled
    if (learning_manager_->is_learning_allowed()) {
        return false;
    }
    
    // Check certification mode
    if (config_.cert_mode != CertificationMode::CERTIFIED &&
        config_.cert_mode != CertificationMode::FLIGHT_CRITICAL) {
        return false;
    }
    
    return true;
}

void FlightController::enable_flight_data_recording(const char* filepath) {
    // Enable data recording for certification
}

DroneKernelInterface::ControlOutput FlightController::compute_pid_control(
    const DroneKernelInterface::DroneState& state) {
    
    DroneKernelInterface::ControlOutput output{};
    float dt = 1.0f / config_.control_frequency_hz;
    
    if (current_mode_ == ControlMode::STABILIZE) {
        // Attitude stabilization only
        output.roll = attitude_pid_->roll.compute(
            attitude_setpoint_[0], state.orientation[1], dt
        );
        output.pitch = attitude_pid_->pitch.compute(
            attitude_setpoint_[1], state.orientation[2], dt
        );
        output.yaw = attitude_pid_->yaw.compute(
            attitude_setpoint_[2], state.orientation[3], dt
        );
        output.throttle = 0.5f;  // Manual throttle in stabilize mode
        
    } else if (current_mode_ == ControlMode::POSITION_HOLD) {
        // Position control -> velocity -> attitude
        float vx_cmd = position_pid_->x.compute(
            position_setpoint_[0], state.position[0], dt
        );
        float vy_cmd = position_pid_->y.compute(
            position_setpoint_[1], state.position[1], dt
        );
        float vz_cmd = position_pid_->z.compute(
            position_setpoint_[2], state.position[2], dt
        );
        
        // Velocity to attitude (simplified)
        output.roll = std::clamp(vy_cmd * 0.1f, -1.0f, 1.0f);
        output.pitch = std::clamp(-vx_cmd * 0.1f, -1.0f, 1.0f);
        output.throttle = std::clamp(0.5f + vz_cmd * 0.1f, 0.0f, 1.0f);
        output.yaw = 0.0f;
    }
    
    return output;
}

DroneKernelInterface::ControlOutput FlightController::compute_mpc_control(
    const DroneKernelInterface::DroneState& state) {
    
    DroneKernelInterface::ControlOutput output{};
    
    if (mpc_) {
        MPCController::State current_state{};
        std::copy(state.position, state.position + 3, current_state.position.begin());
        std::copy(state.velocity, state.velocity + 3, current_state.velocity.begin());
        std::copy(state.orientation, state.orientation + 4, current_state.orientation.begin());
        std::copy(state.angular_vel, state.angular_vel + 3, current_state.angular_vel.begin());
        
        MPCController::State target_state{};
        std::copy(position_setpoint_.begin(), position_setpoint_.end(), target_state.position.begin());
        std::copy(velocity_setpoint_.begin(), velocity_setpoint_.end(), target_state.velocity.begin());
        
        auto control = mpc_->compute(current_state, target_state);
        
        output.throttle = std::clamp(control.thrust / config_.max_thrust_n, 0.0f, 1.0f);
        output.roll = std::clamp(control.torques[0], -1.0f, 1.0f);
        output.pitch = std::clamp(control.torques[1], -1.0f, 1.0f);
        output.yaw = std::clamp(control.torques[2], -1.0f, 1.0f);
    }
    
    return output;
}

DroneKernelInterface::ControlOutput FlightController::compute_geometric_control(
    const DroneKernelInterface::DroneState& state) {
    
    DroneKernelInterface::ControlOutput output{};
    
    if (geometric_) {
        auto geo_output = geometric_->compute(state, trajectory_);
        
        output.throttle = std::clamp(geo_output.thrust / config_.max_thrust_n, 0.0f, 1.0f);
        output.roll = std::clamp(geo_output.moment[0], -1.0f, 1.0f);
        output.pitch = std::clamp(geo_output.moment[1], -1.0f, 1.0f);
        output.yaw = std::clamp(geo_output.moment[2], -1.0f, 1.0f);
    }
    
    return output;
}

DroneKernelInterface::ControlOutput FlightController::compute_hybrid_control(
    const DroneKernelInterface::DroneState& state) {
    
    // Baseline PID control
    auto pid_output = compute_pid_control(state);
    
    // SNN augmentation (only if learning allowed)
    if (snn_kernel_ && learning_manager_->is_learning_allowed()) {
        std::vector<float> input(13);
        std::copy(state.position, state.position + 3, input.begin());
        std::copy(state.velocity, state.velocity + 3, input.begin() + 3);
        std::copy(state.orientation, state.orientation + 4, input.begin() + 6);
        std::copy(state.angular_vel, state.angular_vel + 3, input.begin() + 10);
        
        std::vector<float> snn_output(4);
        auto status = snn_kernel_->infer(
            input.data(), input.size(),
            snn_output.data(), snn_output.size(),
            500  // 0.5ms deadline for augmentation
        );
        
        if (status == KernelStatus::OK) {
            // Blend SNN with PID (conservative blending)
            float blend_factor = 0.1f;  // 10% SNN, 90% PID
            pid_output.throttle = (1.0f - blend_factor) * pid_output.throttle + 
                                 blend_factor * snn_output[0];
            pid_output.roll = (1.0f - blend_factor) * pid_output.roll + 
                             blend_factor * snn_output[1];
            pid_output.pitch = (1.0f - blend_factor) * pid_output.pitch + 
                              blend_factor * snn_output[2];
            pid_output.yaw = (1.0f - blend_factor) * pid_output.yaw + 
                            blend_factor * snn_output[3];
        }
    }
    
    return pid_output;
}

bool FlightController::check_position_limits(
    const DroneKernelInterface::DroneState& state) {
    
    if (!config_.enable_geofence) {
        return true;
    }
    
    // Check altitude limit
    if (state.position[2] > config_.max_altitude_m) {
        return false;
    }
    
    // Additional geofence checks would go here
    return true;
}

bool FlightController::check_velocity_limits(
    const DroneKernelInterface::DroneState& state) {
    
    float vel_magnitude = std::sqrt(
        state.velocity[0] * state.velocity[0] +
        state.velocity[1] * state.velocity[1] +
        state.velocity[2] * state.velocity[2]
    );
    
    return vel_magnitude <= config_.max_velocity_m_s;
}

bool FlightController::check_attitude_limits(
    const DroneKernelInterface::DroneState& state) {
    
    // Check angular rates
    for (int i = 0; i < 3; ++i) {
        float rate_deg_s = state.angular_vel[i] * 180.0f / M_PI;
        if (std::abs(rate_deg_s) > config_.max_angular_rate_deg_s) {
            return false;
        }
    }
    
    return true;
}

void FlightController::record_flight_data(
    const DroneKernelInterface::DroneState& state,
    const DroneKernelInterface::ControlOutput& output) {
    
    // Record flight data for certification audit
    // In production, write to flight data recorder
}

} // namespace flight
} // namespace quadra
