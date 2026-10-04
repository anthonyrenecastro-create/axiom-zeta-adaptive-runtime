#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include "quadra_kernel.hpp"
#include "quadra_supervisory_controller.hpp"

namespace py = pybind11;
using namespace quadra;

// Numpy array conversion helpers
py::array_t<float> vector_to_numpy(const std::vector<float>& vec) {
    return py::array_t<float>(vec.size(), vec.data());
}

std::vector<float> numpy_to_vector(py::array_t<float> arr) {
    py::buffer_info buf = arr.request();
    float* ptr = static_cast<float*>(buf.ptr);
    return std::vector<float>(ptr, ptr + buf.size);
}

PYBIND11_MODULE(quadra_kernel_py, m) {
    m.doc() = "Python bindings for Quadra Matrix SNN Kernel";

    // Enums
    py::enum_<ProcessPriority>(m, "ProcessPriority")
        .value("CRITICAL", ProcessPriority::CRITICAL)
        .value("HIGH", ProcessPriority::HIGH)
        .value("NORMAL", ProcessPriority::NORMAL)
        .value("LOW", ProcessPriority::LOW)
        .export_values();

    py::enum_<KernelStatus>(m, "KernelStatus")
        .value("OK", KernelStatus::OK)
        .value("ERROR_INIT", KernelStatus::ERROR_INIT)
        .value("ERROR_MEMORY", KernelStatus::ERROR_MEMORY)
        .value("ERROR_TIMEOUT", KernelStatus::ERROR_TIMEOUT)
        .value("ERROR_INVALID_INPUT", KernelStatus::ERROR_INVALID_INPUT)
        .value("ERROR_OVERFLOW", KernelStatus::ERROR_OVERFLOW)
        .export_values();

    // SNNKernel::Config
    py::class_<SNNKernel::Config>(m, "KernelConfig")
        .def(py::init<>())
        .def_readwrite("field_size", &SNNKernel::Config::field_size)
        .def_readwrite("num_neurons", &SNNKernel::Config::num_neurons)
        .def_readwrite("learning_rate", &SNNKernel::Config::learning_rate)
        .def_readwrite("use_hardware_acceleration", &SNNKernel::Config::use_hardware_acceleration)
        .def_readwrite("max_inference_time_us", &SNNKernel::Config::max_inference_time_us);

    // SNNKernel::Stats
    py::class_<SNNKernel::Stats>(m, "KernelStats")
        .def(py::init<>())
        .def_readonly("total_inferences", &SNNKernel::Stats::total_inferences)
        .def_readonly("total_spikes", &SNNKernel::Stats::total_spikes)
        .def_readonly("avg_inference_time_us", &SNNKernel::Stats::avg_inference_time_us)
        .def_readonly("field_variance", &SNNKernel::Stats::field_variance)
        .def_readonly("syntropy_level", &SNNKernel::Stats::syntropy_level)
        .def_readonly("missed_deadlines", &SNNKernel::Stats::missed_deadlines);

    // SNNKernel
    py::class_<SNNKernel>(m, "SNNKernel")
        .def(py::init<const SNNKernel::Config&>())
        .def("initialize", &SNNKernel::initialize)
        .def("shutdown", &SNNKernel::shutdown)
        .def("infer", [](SNNKernel& self, py::array_t<float> input, size_t output_size, uint64_t deadline_us) {
            auto input_vec = numpy_to_vector(input);
            std::vector<float> output(output_size);
            auto status = self.infer(input_vec.data(), input_vec.size(), 
                                    output.data(), output_size, deadline_us);
            return py::make_tuple(status, vector_to_numpy(output));
        }, py::arg("input"), py::arg("output_size"), py::arg("deadline_us") = 0)
        .def("train", [](SNNKernel& self, py::array_t<float> data, const std::string& label, uint32_t epochs) {
            auto data_vec = numpy_to_vector(data);
            return self.train(data_vec.data(), data_vec.size(), 
                            label.c_str(), label.size(), epochs);
        }, py::arg("data"), py::arg("label"), py::arg("epochs") = 1)
        .def("get_field_state", [](SNNKernel& self) {
            std::vector<float> state(MAX_FIELD_SIZE);
            size_t state_size = 0;
            auto status = self.get_field_state(state.data(), &state_size);
            state.resize(state_size);
            return py::make_tuple(status, vector_to_numpy(state));
        })
        .def("set_field_state", [](SNNKernel& self, py::array_t<float> state) {
            auto state_vec = numpy_to_vector(state);
            return self.set_field_state(state_vec.data(), state_vec.size());
        })
        .def("get_stats", &SNNKernel::get_stats)
        .def("reset_stats", &SNNKernel::reset_stats)
        .def("is_stable", &SNNKernel::is_stable)
        .def("get_field_resonance", &SNNKernel::get_field_resonance);

    // DroneKernelInterface::DroneState
    py::class_<DroneKernelInterface::DroneState>(m, "DroneState")
        .def(py::init<>())
        .def_property("position",
            [](const DroneKernelInterface::DroneState& self) {
                return py::array_t<float>(3, self.position);
            },
            [](DroneKernelInterface::DroneState& self, py::array_t<float> arr) {
                auto buf = arr.request();
                if (buf.size >= 3) {
                    float* ptr = static_cast<float*>(buf.ptr);
                    std::copy(ptr, ptr + 3, self.position);
                }
            })
        .def_property("velocity",
            [](const DroneKernelInterface::DroneState& self) {
                return py::array_t<float>(3, self.velocity);
            },
            [](DroneKernelInterface::DroneState& self, py::array_t<float> arr) {
                auto buf = arr.request();
                if (buf.size >= 3) {
                    float* ptr = static_cast<float*>(buf.ptr);
                    std::copy(ptr, ptr + 3, self.velocity);
                }
            })
        .def_property("orientation",
            [](const DroneKernelInterface::DroneState& self) {
                return py::array_t<float>(4, self.orientation);
            },
            [](DroneKernelInterface::DroneState& self, py::array_t<float> arr) {
                auto buf = arr.request();
                if (buf.size >= 4) {
                    float* ptr = static_cast<float*>(buf.ptr);
                    std::copy(ptr, ptr + 4, self.orientation);
                }
            })
        .def_property("angular_vel",
            [](const DroneKernelInterface::DroneState& self) {
                return py::array_t<float>(3, self.angular_vel);
            },
            [](DroneKernelInterface::DroneState& self, py::array_t<float> arr) {
                auto buf = arr.request();
                if (buf.size >= 3) {
                    float* ptr = static_cast<float*>(buf.ptr);
                    std::copy(ptr, ptr + 3, self.angular_vel);
                }
            })
        .def_readwrite("timestamp_us", &DroneKernelInterface::DroneState::timestamp_us);

    // DroneKernelInterface::ControlOutput
    py::class_<DroneKernelInterface::ControlOutput>(m, "ControlOutput")
        .def(py::init<>())
        .def_readwrite("throttle", &DroneKernelInterface::ControlOutput::throttle)
        .def_readwrite("roll", &DroneKernelInterface::ControlOutput::roll)
        .def_readwrite("pitch", &DroneKernelInterface::ControlOutput::pitch)
        .def_readwrite("yaw", &DroneKernelInterface::ControlOutput::yaw)
        .def_readwrite("emergency_stop", &DroneKernelInterface::ControlOutput::emergency_stop);

    // DroneKernelInterface
    py::class_<DroneKernelInterface>(m, "DroneKernelInterface")
        .def(py::init<SNNKernel*>())
        .def("process_control_cycle", &DroneKernelInterface::process_control_cycle)
        .def("fuse_sensor_data", [](DroneKernelInterface& self, 
                                    py::array_t<float> imu_data,
                                    py::array_t<float> vision_data) {
            auto imu_vec = numpy_to_vector(imu_data);
            auto vision_vec = numpy_to_vector(vision_data);
            DroneKernelInterface::DroneState fused_state;
            
            auto status = self.fuse_sensor_data(
                imu_vec.data(), imu_vec.size(),
                vision_vec.data(), vision_vec.size(),
                fused_state
            );
            
            return py::make_tuple(status, fused_state);
        })
        .def("detect_collision_risk", [](DroneKernelInterface& self, py::array_t<float> obstacle_data) {
            auto data_vec = numpy_to_vector(obstacle_data);
            float risk_score = 0.0f;
            bool at_risk = self.detect_collision_risk(data_vec.data(), data_vec.size(), risk_score);
            return py::make_tuple(at_risk, risk_score);
        })
        .def("update_pid_gains", &DroneKernelInterface::update_pid_gains);

    // KernelMemoryInterface (singleton)
    py::class_<KernelMemoryInterface>(m, "KernelMemoryInterface")
        .def_static("instance", &KernelMemoryInterface::instance, py::return_value_policy::reference)
        .def("write_register", &KernelMemoryInterface::write_register)
        .def("read_register", &KernelMemoryInterface::read_register)
        .def("has_snn_accelerator", &KernelMemoryInterface::has_snn_accelerator);

    // Module-level constants
    m.attr("MAX_FIELD_SIZE") = MAX_FIELD_SIZE;
    m.attr("MAX_NEURONS") = MAX_NEURONS;
    m.attr("MAX_BATCH_SIZE") = MAX_BATCH_SIZE;
    m.attr("STABILITY_THRESHOLD") = STABILITY_THRESHOLD;

    // ========================================================================
    // Supervisory Controller Bindings
    // ========================================================================
    
    using namespace supervisory;
    
    // SupervisoryConfig
    py::class_<SupervisoryConfig>(m, "SupervisoryConfig")
        .def(py::init<>())
        .def_readwrite("field_size", &SupervisoryConfig::field_size)
        .def_readwrite("update_frequency_hz", &SupervisoryConfig::update_frequency_hz)
        .def_readwrite("learning_rate", &SupervisoryConfig::learning_rate)
        .def_readwrite("cert_mode", &SupervisoryConfig::cert_mode)
        .def_readwrite("enable_adaptation", &SupervisoryConfig::enable_adaptation)
        .def_readwrite("enable_plasticity", &SupervisoryConfig::enable_plasticity)
        .def_readwrite("maintain_variance_feedback", &SupervisoryConfig::maintain_variance_feedback)
        .def_readwrite("use_noise_injection_stress_test", &SupervisoryConfig::use_noise_injection_stress_test)
        .def_readwrite("require_stability_for_adaptation", &SupervisoryConfig::require_stability_for_adaptation)
        .def_readwrite("min_stability_threshold", &SupervisoryConfig::min_stability_threshold);
    
    // SupervisoryState
    py::class_<SupervisoryState>(m, "SupervisoryState")
        .def(py::init<>())
        .def_readwrite("timestamp_us", &SupervisoryState::timestamp_us)
        .def_property("imu_residuals",
            [](const SupervisoryState& self) {
                return py::array_t<float>(3, self.imu_residuals);
            },
            [](SupervisoryState& self, py::array_t<float> arr) {
                auto buf = arr.request();
                if (buf.size >= 3) {
                    float* ptr = static_cast<float*>(buf.ptr);
                    std::copy(ptr, ptr + 3, self.imu_residuals);
                }
            })
        .def_property("wind_estimate_error",
            [](const SupervisoryState& self) {
                return py::array_t<float>(3, self.wind_estimate_error);
            },
            [](SupervisoryState& self, py::array_t<float> arr) {
                auto buf = arr.request();
                if (buf.size >= 3) {
                    float* ptr = static_cast<float*>(buf.ptr);
                    std::copy(ptr, ptr + 3, self.wind_estimate_error);
                }
            })
        .def_readwrite("control_effort_variance", &SupervisoryState::control_effort_variance)
        .def_readwrite("state_estimator_uncertainty", &SupervisoryState::state_estimator_uncertainty)
        .def_readwrite("tracking_error", &SupervisoryState::tracking_error)
        .def_readwrite("stability_margin", &SupervisoryState::stability_margin)
        .def_readwrite("disturbance_rejection", &SupervisoryState::disturbance_rejection)
        .def_readwrite("field_mean", &SupervisoryState::field_mean)
        .def_readwrite("field_variance", &SupervisoryState::field_variance)
        .def_readwrite("syntropy_level", &SupervisoryState::syntropy_level)
        .def_property("field_state",
            [](const SupervisoryState& self) {
                return py::array_t<float>(self.field_state.size(), self.field_state.data());
            },
            [](SupervisoryState& self, py::array_t<float> arr) {
                self.field_state = numpy_to_vector(arr);
            });
    
    // GainSchedule
    py::class_<AdaptiveParameters::GainSchedule>(m, "GainSchedule")
        .def(py::init<>())
        .def_readwrite("position_kp_scale", &AdaptiveParameters::GainSchedule::position_kp_scale)
        .def_readwrite("attitude_kp_scale", &AdaptiveParameters::GainSchedule::attitude_kp_scale)
        .def_readwrite("altitude_kp_scale", &AdaptiveParameters::GainSchedule::altitude_kp_scale)
        .def_readwrite("derivative_gain_scale", &AdaptiveParameters::GainSchedule::derivative_gain_scale)
        .def_readwrite("integral_limit_scale", &AdaptiveParameters::GainSchedule::integral_limit_scale);
    
    // ControlEnvelope
    py::class_<AdaptiveParameters::ControlEnvelope>(m, "ControlEnvelope")
        .def(py::init<>())
        .def_readwrite("max_tilt_angle_deg", &AdaptiveParameters::ControlEnvelope::max_tilt_angle_deg)
        .def_readwrite("max_vertical_speed", &AdaptiveParameters::ControlEnvelope::max_vertical_speed)
        .def_readwrite("max_horizontal_speed", &AdaptiveParameters::ControlEnvelope::max_horizontal_speed)
        .def_readwrite("max_yaw_rate", &AdaptiveParameters::ControlEnvelope::max_yaw_rate);
    
    // ModeSwitching
    py::class_<AdaptiveParameters::ModeSwitching>(m, "ModeSwitching")
        .def(py::init<>())
        .def_readwrite("aggressive_mode_threshold", &AdaptiveParameters::ModeSwitching::aggressive_mode_threshold)
        .def_readwrite("conservative_mode_threshold", &AdaptiveParameters::ModeSwitching::conservative_mode_threshold)
        .def_readwrite("gps_weight_schedule", &AdaptiveParameters::ModeSwitching::gps_weight_schedule)
        .def_readwrite("position_hold_tolerance", &AdaptiveParameters::ModeSwitching::position_hold_tolerance);
    
    // ExplorationParams
    py::class_<AdaptiveParameters::ExplorationParams>(m, "ExplorationParams")
        .def(py::init<>())
        .def_readwrite("exploration_rate", &AdaptiveParameters::ExplorationParams::exploration_rate)
        .def_readwrite("noise_injection_level", &AdaptiveParameters::ExplorationParams::noise_injection_level)
        .def_readwrite("adaptation_rate", &AdaptiveParameters::ExplorationParams::adaptation_rate)
        .def_readwrite("confidence_threshold", &AdaptiveParameters::ExplorationParams::confidence_threshold);
    
    // AdaptiveParameters
    py::class_<AdaptiveParameters>(m, "AdaptiveParameters")
        .def(py::init<>())
        .def_readwrite("gain_schedule", &AdaptiveParameters::gain_schedule)
        .def_readwrite("control_envelope", &AdaptiveParameters::control_envelope)
        .def_readwrite("mode_switching", &AdaptiveParameters::mode_switching)
        .def_readwrite("exploration", &AdaptiveParameters::exploration);
    
    // FieldDynamicsProcessor
    py::class_<FieldDynamicsProcessor>(m, "FieldDynamicsProcessor")
        .def(py::init<size_t>())
        .def("update_field", [](FieldDynamicsProcessor& self, py::array_t<float> input) {
            auto vec = numpy_to_vector(input);
            self.update_field(vec.data(), vec.size());
        })
        .def("regulate_variance", &FieldDynamicsProcessor::regulate_variance)
        .def("apply_plasticity", &FieldDynamicsProcessor::apply_plasticity)
        .def("inject_stress_test_noise", &FieldDynamicsProcessor::inject_stress_test_noise)
        .def("get_field_mean", &FieldDynamicsProcessor::get_field_mean)
        .def("get_field_variance", &FieldDynamicsProcessor::get_field_variance)
        .def("get_syntropy_level", &FieldDynamicsProcessor::get_syntropy_level)
        .def("compute_adaptation_rate", &FieldDynamicsProcessor::compute_adaptation_rate)
        .def("is_field_stable", &FieldDynamicsProcessor::is_field_stable)
        .def("get_field_state", [](const FieldDynamicsProcessor& self) {
            const auto& state = self.get_field_state();
            return py::array_t<float>(state.size(), state.data());
        });
    
    // SupervisoryController::Statistics
    py::class_<SupervisoryController::Statistics>(m, "SupervisoryStatistics")
        .def(py::init<>())
        .def_readwrite("total_updates", &SupervisoryController::Statistics::total_updates)
        .def_readwrite("parameter_changes", &SupervisoryController::Statistics::parameter_changes)
        .def_readwrite("avg_update_time_ms", &SupervisoryController::Statistics::avg_update_time_ms)
        .def_readwrite("field_stability", &SupervisoryController::Statistics::field_stability)
        .def_readwrite("adaptation_confidence", &SupervisoryController::Statistics::adaptation_confidence);
    
    // SupervisoryController
    py::class_<SupervisoryController>(m, "SupervisoryController")
        .def(py::init<const SupervisoryConfig&, flight::FlightController*>())
        .def("initialize", &SupervisoryController::initialize)
        .def("update", &SupervisoryController::update)
        .def("get_current_state", &SupervisoryController::get_current_state)
        .def("get_statistics", &SupervisoryController::get_statistics)
        .def("get_adaptive_parameters", &SupervisoryController::get_adaptive_parameters)
        .def("enable_adaptation", &SupervisoryController::enable_adaptation)
        .def("reset_to_defaults", &SupervisoryController::reset_to_defaults);
    
    // SupervisoryIntegration
    py::class_<SupervisoryIntegration>(m, "SupervisoryIntegration")
        .def(py::init<flight::FlightController*, const SupervisoryConfig&>())
        .def("start", &SupervisoryIntegration::start)
        .def("stop", &SupervisoryIntegration::stop)
        .def("get_supervisor", &SupervisoryIntegration::get_supervisor,
             py::return_value_policy::reference);
}
