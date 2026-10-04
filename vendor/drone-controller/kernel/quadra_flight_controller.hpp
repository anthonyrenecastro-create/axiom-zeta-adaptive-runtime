#ifndef QUADRA_FLIGHT_CONTROLLER_HPP
#define QUADRA_FLIGHT_CONTROLLER_HPP

/**
 * @file quadra_flight_controller.hpp
 * @brief Production-grade flight controllers for certified drone systems
 * 
 * Implements:
 * - PID Controller (DO-178C compliant)
 * - Model Predictive Control (MPC)
 * - Geometric Controller on SE(3)
 * - Fixed-rate execution (200Hz-1kHz)
 * - Deterministic behavior for certification
 * - Safe, limited learning modes
 */

#include "quadra_kernel.hpp"
#include <array>
#include <vector>
#include <chrono>
#include <cmath>

namespace quadra {
namespace flight {

// ============================================================================
// Control Modes and Configuration
// ============================================================================

enum class ControlMode {
    MANUAL,           // Direct pass-through
    STABILIZE,        // Angle stabilization
    ALTITUDE_HOLD,    // Altitude + attitude control
    POSITION_HOLD,    // Full position control
    AUTONOMOUS,       // Waypoint navigation
    GUIDED           // External guidance
};

enum class ControllerType {
    PID,              // Classic PID
    MPC,              // Model Predictive Control
    GEOMETRIC,        // SE(3) geometric controller
    HYBRID_SNN_PID    // SNN-augmented PID
};

/**
 * @brief Certification mode settings
 */
enum class CertificationMode {
    DEVELOPMENT,      // Full learning, non-deterministic
    TESTING,          // Limited learning, logging enabled
    CERTIFIED,        // No online learning, fully deterministic
    FLIGHT_CRITICAL   // Minimal features, maximum reliability
};

/**
 * @brief Safe learning modes (only active when not in CERTIFIED mode)
 */
enum class LearningMode {
    DISABLED,                    // No learning
    TARGET_TRACKING,             // Track moving targets
    SENSOR_FUSION_WEIGHTS,       // Adapt sensor trust
    CONTROL_TIMING,              // Optimize control timing
    ENVIRONMENTAL_COMPENSATION   // Wind/turbulence adaptation
};

// ============================================================================
// Flight Controller Configuration
// ============================================================================

struct FlightControllerConfig {
    // Execution timing
    uint32_t control_frequency_hz = 400;  // 200-1000 Hz
    uint32_t max_jitter_us = 50;          // Maximum timing jitter
    bool enforce_hard_realtime = true;    // Hard RT constraints
    
    // Certification settings
    CertificationMode cert_mode = CertificationMode::DEVELOPMENT;
    bool enable_deterministic_mode = false;
    uint64_t prng_seed = 42;  // Fixed seed for deterministic behavior
    
    // Learning configuration
    LearningMode learning_mode = LearningMode::DISABLED;
    float learning_rate_limit = 0.001f;  // Max learning rate
    bool require_learning_approval = true;
    
    // Controller selection
    ControllerType controller_type = ControllerType::PID;
    ControlMode control_mode = ControlMode::STABILIZE;
    
    // Vehicle parameters
    float mass_kg = 1.5f;
    float max_thrust_n = 25.0f;
    float max_angle_deg = 30.0f;
    float max_angular_rate_deg_s = 200.0f;
    
    // Safety limits
    float max_velocity_m_s = 15.0f;
    float max_altitude_m = 120.0f;
    bool enable_geofence = true;
};

// ============================================================================
// PID Controller (DO-178C compliant)
// ============================================================================

/**
 * @brief Certified PID controller with anti-windup
 */
class PIDController {
public:
    struct Gains {
        float kp = 1.0f;
        float ki = 0.1f;
        float kd = 0.05f;
        float i_max = 10.0f;  // Integrator clamp
        float output_max = 1.0f;
    };
    
    PIDController(const Gains& gains);
    ~PIDController() = default;
    
    // Non-copyable for certification compliance
    PIDController(const PIDController&) = delete;
    PIDController& operator=(const PIDController&) = delete;
    
    float compute(float setpoint, float measurement, float dt);
    void reset();
    void set_gains(const Gains& gains);
    Gains get_gains() const;
    
    // Diagnostics (certification requirement)
    float get_p_term() const { return p_term_; }
    float get_i_term() const { return i_term_; }
    float get_d_term() const { return d_term_; }
    float get_error() const { return error_; }
    
private:
    Gains gains_;
    float integral_ = 0.0f;
    float prev_error_ = 0.0f;
    float error_ = 0.0f;
    float p_term_ = 0.0f;
    float i_term_ = 0.0f;
    float d_term_ = 0.0f;
    
    // Anti-windup
    void clamp_integral();
};

// ============================================================================
// Axis-specific PID Controllers
// ============================================================================

struct AttitudePIDControllers {
    PIDController roll;
    PIDController pitch;
    PIDController yaw;
    
    AttitudePIDControllers(
        const PIDController::Gains& roll_gains,
        const PIDController::Gains& pitch_gains,
        const PIDController::Gains& yaw_gains
    );
};

struct PositionPIDControllers {
    PIDController x;
    PIDController y;
    PIDController z;
    
    PositionPIDControllers(
        const PIDController::Gains& xy_gains,
        const PIDController::Gains& z_gains
    );
};

// ============================================================================
// Model Predictive Controller (MPC)
// ============================================================================

/**
 * @brief Linear MPC for trajectory tracking
 */
class MPCController {
public:
    struct Config {
        size_t prediction_horizon = 10;
        size_t control_horizon = 5;
        float dt = 0.01f;  // Discretization time
        
        // Cost weights
        float position_weight = 10.0f;
        float velocity_weight = 1.0f;
        float control_weight = 0.1f;
        float control_rate_weight = 0.05f;
    };
    
    MPCController(const Config& config);
    ~MPCController();
    
    struct State {
        std::array<float, 3> position;
        std::array<float, 3> velocity;
        std::array<float, 4> orientation;
        std::array<float, 3> angular_vel;
    };
    
    struct Control {
        float thrust;
        std::array<float, 3> torques;
    };
    
    Control compute(const State& current, const State& target);
    void set_constraints(float max_thrust, float max_torque);
    
private:
    Config config_;
    std::vector<State> predicted_states_;
    std::vector<Control> control_sequence_;
    
    void solve_qp();  // Quadratic Programming solver
    void linearize_dynamics(const State& state);
};

// ============================================================================
// Geometric Controller (SE(3))
// ============================================================================

/**
 * @brief Geometric tracking controller on SE(3)
 * 
 * Reference: Lee et al., "Geometric tracking control of a quadrotor UAV 
 * on SE(3)", CDC 2010
 */
class GeometricController {
public:
    struct Gains {
        // Position control gains
        float kx = 8.0f;    // Position error
        float kv = 4.0f;    // Velocity error
        
        // Attitude control gains
        float kR = 2.5f;    // Rotation error
        float kOmega = 1.0f; // Angular velocity error
        
        float mass = 1.5f;
        float gravity = 9.81f;
    };
    
    GeometricController(const Gains& gains);
    ~GeometricController() = default;
    
    struct Trajectory {
        std::array<float, 3> position;
        std::array<float, 3> velocity;
        std::array<float, 3> acceleration;
        float yaw;
        float yaw_rate;
    };
    
    struct Output {
        float thrust;              // Total thrust (N)
        std::array<float, 3> moment;  // Body moments (Nm)
    };
    
    Output compute(
        const DroneKernelInterface::DroneState& state,
        const Trajectory& desired
    );
    
private:
    Gains gains_;
    
    // Rotation matrix from quaternion
    std::array<std::array<float, 3>, 3> quat_to_rotation_matrix(
        const std::array<float, 4>& q
    ) const;
    
    // SO(3) error
    std::array<float, 3> rotation_error(
        const std::array<std::array<float, 3>, 3>& R,
        const std::array<std::array<float, 3>, 3>& Rd
    ) const;
};

// ============================================================================
// Fixed-Rate Execution Manager
// ============================================================================

/**
 * @brief Ensures deterministic fixed-rate execution
 */
class FixedRateExecutor {
public:
    FixedRateExecutor(uint32_t frequency_hz, uint32_t max_jitter_us);
    ~FixedRateExecutor() = default;
    
    bool begin_cycle();  // Start of control cycle
    bool end_cycle();    // End of control cycle, sleeps if needed
    
    struct Statistics {
        uint64_t total_cycles = 0;
        uint64_t missed_deadlines = 0;
        float avg_cycle_time_us = 0.0f;
        float max_cycle_time_us = 0.0f;
        float jitter_us = 0.0f;
    };
    
    Statistics get_statistics() const;
    void reset_statistics();
    
private:
    uint32_t frequency_hz_;
    uint32_t max_jitter_us_;
    uint64_t cycle_period_us_;
    
    std::chrono::steady_clock::time_point cycle_start_;
    std::chrono::steady_clock::time_point last_cycle_end_;
    
    Statistics stats_;
};

// ============================================================================
// Safe Learning Manager
// ============================================================================

/**
 * @brief Manages safe, limited learning in non-certified modes
 */
class SafeLearningManager {
public:
    SafeLearningManager(const FlightControllerConfig& config);
    ~SafeLearningManager() = default;
    
    bool is_learning_allowed() const;
    bool can_update_parameter(const char* param_name) const;
    
    // Safe learning operations
    bool update_target_tracking(float* tracking_gains, size_t size);
    bool update_sensor_fusion_weights(float* weights, size_t num_sensors);
    bool adapt_control_timing(float& dt_adjustment);
    bool compensate_environment(float* compensation, size_t size);
    
    // Approval system
    bool request_learning_approval(const char* reason);
    void log_learning_event(const char* event, float* data, size_t size);
    
private:
    FlightControllerConfig config_;
    bool learning_approved_ = false;
    uint64_t last_learning_time_us_ = 0;
    
    bool is_parameter_whitelisted(const char* param_name) const;
};

// ============================================================================
// Integrated Flight Controller
// ============================================================================

/**
 * @brief Main flight controller integrating all components
 */
class FlightController {
public:
    FlightController(
        const FlightControllerConfig& config,
        SNNKernel* snn_kernel = nullptr
    );
    ~FlightController();
    
    // Initialize controller
    KernelStatus initialize();
    
    // Main control loop - call at fixed rate
    KernelStatus control_step(
        const DroneKernelInterface::DroneState& state,
        DroneKernelInterface::ControlOutput& output
    );
    
    // Setpoint control
    void set_position_setpoint(float x, float y, float z);
    void set_velocity_setpoint(float vx, float vy, float vz);
    void set_attitude_setpoint(float roll, float pitch, float yaw);
    void set_trajectory(const GeometricController::Trajectory& traj);
    
    // Mode changes
    void set_control_mode(ControlMode mode);
    void set_controller_type(ControllerType type);
    
    // Safety
    bool check_safety_limits(const DroneKernelInterface::DroneState& state);
    void emergency_stop();
    
    // Diagnostics
    FixedRateExecutor::Statistics get_timing_stats() const;
    void get_pid_diagnostics(char* buffer, size_t buffer_size) const;
    
    // Certification compliance
    bool verify_deterministic_behavior() const;
    void enable_flight_data_recording(const char* filepath);
    
private:
    FlightControllerConfig config_;
    SNNKernel* snn_kernel_;
    
    // Controllers
    std::unique_ptr<AttitudePIDControllers> attitude_pid_;
    std::unique_ptr<PositionPIDControllers> position_pid_;
    std::unique_ptr<MPCController> mpc_;
    std::unique_ptr<GeometricController> geometric_;
    
    // Execution management
    std::unique_ptr<FixedRateExecutor> executor_;
    std::unique_ptr<SafeLearningManager> learning_manager_;
    
    // Setpoints
    std::array<float, 3> position_setpoint_;
    std::array<float, 3> velocity_setpoint_;
    std::array<float, 3> attitude_setpoint_;
    GeometricController::Trajectory trajectory_;
    
    // State
    bool initialized_ = false;
    bool emergency_stop_ = false;
    ControlMode current_mode_;
    
    // Internal control methods
    DroneKernelInterface::ControlOutput compute_pid_control(
        const DroneKernelInterface::DroneState& state
    );
    
    DroneKernelInterface::ControlOutput compute_mpc_control(
        const DroneKernelInterface::DroneState& state
    );
    
    DroneKernelInterface::ControlOutput compute_geometric_control(
        const DroneKernelInterface::DroneState& state
    );
    
    DroneKernelInterface::ControlOutput compute_hybrid_control(
        const DroneKernelInterface::DroneState& state
    );
    
    // Safety checks
    bool check_position_limits(const DroneKernelInterface::DroneState& state);
    bool check_velocity_limits(const DroneKernelInterface::DroneState& state);
    bool check_attitude_limits(const DroneKernelInterface::DroneState& state);
    
    // Data recording for certification
    void record_flight_data(
        const DroneKernelInterface::DroneState& state,
        const DroneKernelInterface::ControlOutput& output
    );
};

} // namespace flight
} // namespace quadra

#endif // QUADRA_FLIGHT_CONTROLLER_HPP
