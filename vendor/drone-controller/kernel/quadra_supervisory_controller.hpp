#ifndef QUADRA_SUPERVISORY_CONTROLLER_HPP
#define QUADRA_SUPERVISORY_CONTROLLER_HPP

/**
 * @file quadra_supervisory_controller.hpp
 * @brief Supervisory learning layer for high-level parameter adaptation
 * 
 * This layer:
 * - Runs at 5-20 Hz (slower than main control loop)
 * - Uses SNN field dynamics with drone-specific inputs
 * - Adjusts gain schedules, envelopes, thresholds
 * - NEVER directly commands motors
 * - Preserves original field dynamics, variance regulation, plasticity
 */

#include "quadra_kernel.hpp"
#include "quadra_flight_controller.hpp"
#include <array>
#include <vector>
#include <deque>

namespace quadra {
namespace supervisory {

// ============================================================================
// Supervisory State - Extended Field State
// ============================================================================

/**
 * @brief Extended state fed into SNN field dynamics
 * Preserves original field dynamics while adding drone-specific inputs
 */
struct SupervisoryState {
    // Original SNN field state (preserved)
    std::vector<float> field_state;          // Core field dynamics
    float field_mean = 0.0f;                 // Mean (regulated)
    float field_variance = 0.0f;             // Variance (maintained by feedback)
    float syntropy_level = 0.0f;             // Order emergence
    
    // Drone-specific additions to field state
    std::array<float, 3> imu_residuals;      // IMU prediction error
    std::array<float, 3> wind_estimate_error; // Wind estimation uncertainty
    float control_effort_variance = 0.0f;     // Control signal variability
    float state_estimator_uncertainty = 0.0f; // Kalman filter uncertainty
    
    // Performance metrics (input to field)
    float tracking_error = 0.0f;
    float stability_margin = 0.0f;
    float disturbance_rejection = 0.0f;
    
    // Timestamped for slow update rate
    uint64_t timestamp_us = 0;
};

// ============================================================================
// Adaptable Parameters - Never Direct Motor Commands
// ============================================================================

/**
 * @brief Parameters adjusted by supervisory controller
 * These affect control behavior but NEVER directly command motors
 */
struct AdaptiveParameters {
    // Gain schedules
    struct GainSchedule {
        float position_kp_scale = 1.0f;      // Scale factor for position PID
        float attitude_kp_scale = 1.0f;      // Scale factor for attitude PID
        float altitude_kp_scale = 1.0f;      // Scale factor for altitude PID
        float derivative_gain_scale = 1.0f;  // D-term scaling
        float integral_limit_scale = 1.0f;   // I-term limit scaling
    } gain_schedule;
    
    // Control envelopes (safety bounds)
    struct ControlEnvelope {
        float max_tilt_angle_deg = 30.0f;    // Maximum allowed tilt
        float max_vertical_speed = 5.0f;     // m/s
        float max_horizontal_speed = 10.0f;  // m/s
        float max_yaw_rate = 90.0f;          // deg/s
    } control_envelope;
    
    // Mode switching thresholds
    struct ModeSwitching {
        float aggressive_mode_threshold = 0.8f;  // Stability before aggressive
        float conservative_mode_threshold = 0.3f; // Switch to conservative
        float gps_weight_schedule = 0.7f;         // GPS vs vision weight
        float position_hold_tolerance = 0.5f;     // Position hold deadband (m)
    } mode_switching;
    
    // Exploration vs exploitation
    struct ExplorationParams {
        float exploration_rate = 0.1f;       // How much to explore
        float noise_injection_level = 0.05f; // Stress-test noise level
        float adaptation_rate = 0.01f;       // How fast to adapt
        float confidence_threshold = 0.7f;   // When to trust learned params
    } exploration;
    
    // Bounds for safety
    static constexpr float MIN_GAIN_SCALE = 0.3f;
    static constexpr float MAX_GAIN_SCALE = 2.0f;
};

// ============================================================================
// Supervisory Controller Configuration
// ============================================================================

struct SupervisoryConfig {
    // Update rate (much slower than main control)
    uint32_t update_frequency_hz = 10;  // 5-20 Hz
    
    // SNN field configuration (preserved from original)
    size_t field_size = 100;
    bool maintain_variance_feedback = true;
    bool enable_plasticity = true;
    bool use_noise_injection_stress_test = true;
    
    // Learning rate (for parameter adaptation)
    float learning_rate = 0.01f;
    float plasticity_rate = 0.001f;  // Original plasticity mechanism
    
    // Safety and certification
    flight::CertificationMode cert_mode = flight::CertificationMode::DEVELOPMENT;
    bool enable_adaptation = true;
    bool require_stability_for_adaptation = true;
    float min_stability_threshold = 0.5f;
};

// ============================================================================
// Field Dynamics Processor (Preserves Original Mechanisms)
// ============================================================================

/**
 * @brief Maintains original SNN field dynamics
 * This class is NEVER modified - preserves core functionality
 */
class FieldDynamicsProcessor {
public:
    FieldDynamicsProcessor(size_t field_size);
    ~FieldDynamicsProcessor() = default;
    
    // Core dynamics (preserved from original)
    void update_field(const float* input, size_t input_size);
    void regulate_variance();  // Feedback loop maintaining variance
    void apply_plasticity(float reward);  // Plasticity update mechanism
    void inject_stress_test_noise(float intensity);  // Noise as stress-testing
    
    // Field state access (read-only)
    const std::vector<float>& get_field_state() const { return field_state_; }
    float get_field_mean() const;
    float get_field_variance() const;
    float get_syntropy_level() const;
    
    // Rate control based on internal state (preserved)
    float compute_adaptation_rate() const;
    bool is_field_stable() const;
    
private:
    std::vector<float> field_state_;
    size_t field_size_;
    
    // Variance regulation state (preserved)
    float target_variance_ = 0.05f;
    float variance_feedback_gain_ = 0.1f;
    
    // Plasticity state (preserved)
    std::vector<float> plasticity_traces_;
    float base_plasticity_rate_ = 0.001f;
    
    // Internal rate control (preserved)
    float internal_excitation_ = 0.0f;
    
    // Stress-test noise generator
    std::mt19937 noise_gen_;
    
    // Private helpers (preserved mechanisms)
    void apply_variance_feedback();
    void update_plasticity_traces();
    float compute_internal_rate() const;
};

// ============================================================================
// Supervisory Controller - Slow Adaptive Layer
// ============================================================================

/**
 * @brief High-level supervisory controller (5-20 Hz)
 * 
 * This layer:
 * - Uses SNN field dynamics (preserved)
 * - Adds drone-specific state to field input
 * - Adjusts high-level parameters
 * - Never directly commands motors
 * - Can tolerate variability
 */
class SupervisoryController {
public:
    SupervisoryController(
        const SupervisoryConfig& config,
        flight::FlightController* flight_controller
    );
    ~SupervisoryController();
    
    // Initialize supervisory layer
    KernelStatus initialize();
    
    // Main supervisory update (call at 5-20 Hz)
    void update(const SupervisoryState& state);
    
    // Get current adaptive parameters
    const AdaptiveParameters& get_adaptive_parameters() const {
        return adaptive_params_;
    }
    
    // Apply parameters to flight controller
    void apply_parameters_to_controller();
    
    // Field state query (for monitoring)
    SupervisoryState get_current_state() const;
    
    // Statistics
    struct Statistics {
        uint64_t total_updates = 0;
        uint64_t parameter_changes = 0;
        float avg_update_time_ms = 0.0f;
        float field_stability = 0.0f;
        float adaptation_confidence = 0.0f;
    };
    
    Statistics get_statistics() const;
    
    // Control
    void enable_adaptation(bool enable);
    void reset_to_defaults();
    
private:
    SupervisoryConfig config_;
    flight::FlightController* flight_controller_;
    
    // Core SNN field processor (preserved dynamics)
    std::unique_ptr<FieldDynamicsProcessor> field_processor_;
    
    // Current state
    SupervisoryState current_state_;
    AdaptiveParameters adaptive_params_;
    
    // Learning history
    std::deque<SupervisoryState> state_history_;
    std::deque<float> performance_history_;
    
    // Statistics
    Statistics stats_;
    
    // State estimation
    void estimate_imu_residuals(const SupervisoryState& state);
    void estimate_wind_error(const SupervisoryState& state);
    void compute_control_effort_variance();
    void compute_state_uncertainty();
    
    // Field input construction
    std::vector<float> construct_field_input(const SupervisoryState& state);
    
    // Parameter adaptation (slow, high-level)
    void adapt_gain_schedule(float reward);
    void adapt_control_envelope(float safety_margin);
    void adapt_mode_switching(float performance_metric);
    void adapt_exploration_params(float confidence);
    
    // Safety checks
    bool is_safe_to_adapt() const;
    void enforce_parameter_bounds();
    
    // Reward computation
    float compute_reward() const;
};

// ============================================================================
// Integration Helper
// ============================================================================

/**
 * @brief Helper to integrate supervisory controller with flight stack
 */
class SupervisoryIntegration {
public:
    SupervisoryIntegration(
        flight::FlightController* flight_controller,
        const SupervisoryConfig& config
    );
    ~SupervisoryIntegration();
    
    // Call this at main control loop rate (200-1000 Hz)
    void fast_control_callback(
        const flight::DroneKernelInterface::DroneState& state,
        const flight::DroneKernelInterface::ControlOutput& output
    );
    
    // Supervisory update happens automatically at slow rate
    void run_supervisory_thread();
    
    // Control
    void start();
    void stop();
    
private:
    std::unique_ptr<SupervisoryController> supervisor_;
    flight::FlightController* flight_controller_;
    
    // State accumulation for supervisory layer
    struct AccumulatedState {
        std::vector<std::array<float, 3>> imu_errors;
        std::vector<float> control_efforts;
        float wind_x_estimate = 0.0f;
        float wind_y_estimate = 0.0f;
        float wind_z_estimate = 0.0f;
    } accumulated_;
    
    // Threading for slow supervisory updates
    std::thread supervisory_thread_;
    std::atomic<bool> running_{false};
    std::mutex state_mutex_;
    
    // Timing
    std::chrono::steady_clock::time_point last_update_;
    uint64_t update_period_ms_;
    
    // Build supervisory state from accumulated data
    SupervisoryState build_supervisory_state();
    
    // Accumulate fast-loop data
    void accumulate_state_data(
        const flight::DroneKernelInterface::DroneState& state,
        const flight::DroneKernelInterface::ControlOutput& output
    );
};

} // namespace supervisory
} // namespace quadra

#endif // QUADRA_SUPERVISORY_CONTROLLER_HPP
