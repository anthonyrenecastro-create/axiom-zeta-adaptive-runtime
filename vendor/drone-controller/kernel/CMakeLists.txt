cmake_minimum_required(VERSION 3.15)
project(QuadraKernel VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Options
option(BUILD_PYTHON_BINDINGS "Build Python bindings" ON)
option(BUILD_TESTS "Build tests" ON)
option(BUILD_EXAMPLES "Build examples" ON)
option(ENABLE_RTOS_SUPPORT "Enable RTOS compatibility layer" ON)
option(ENABLE_HARDWARE_ACCEL "Enable hardware acceleration hooks" OFF)

# Set build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wpedantic")
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -DDEBUG")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -DNDEBUG")
set(CMAKE_CXX_FLAGS_RELWITHDEBINFO "-O2 -g")

# Find required packages
find_package(Threads REQUIRED)

# Core library
add_library(quadra_kernel SHARED
    quadra_kernel.cpp
    quadra_kernel.hpp
    quadra_flight_controller.cpp
    quadra_flight_controller.hpp
    quadra_supervisory_controller.cpp
    quadra_supervisory_controller.hpp
)

target_include_directories(quadra_kernel PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<INSTALL_INTERFACE:include>
)

target_link_libraries(quadra_kernel
    PUBLIC
        Threads::Threads
    PRIVATE
        m  # Math library
)

# RTOS support (header-only)
if(ENABLE_RTOS_SUPPORT)
    target_compile_definitions(quadra_kernel PUBLIC QUADRA_RTOS_ENABLED)
endif()

# Python bindings
if(BUILD_PYTHON_BINDINGS)
    find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
    
    # Try to find pybind11
    find_package(pybind11 CONFIG QUIET)
    
    if(NOT pybind11_FOUND)
        # Fallback: download pybind11
        include(FetchContent)
        FetchContent_Declare(
            pybind11
            GIT_REPOSITORY https://github.com/pybind/pybind11
            GIT_TAG v2.11.1
        )
        FetchContent_MakeAvailable(pybind11)
    endif()
    
    pybind11_add_module(quadra_kernel_py python_bindings.cpp)
    target_link_libraries(quadra_kernel_py PRIVATE quadra_kernel)
    
    # Install Python module
    install(TARGETS quadra_kernel_py
        LIBRARY DESTINATION ${Python3_SITEARCH}
    )
    
    # Install Python wrapper
    install(FILES quadra_kernel.py
        DESTINATION ${Python3_SITEARCH}
    )
endif()

# Examples
if(BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()

# Tests
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# Installation
install(TARGETS quadra_kernel
    EXPORT QuadraKernelTargets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(FILES
    quadra_kernel.hpp
    quadra_rtos.hpp
    quadra_flight_controller.hpp
    DESTINATION include/quadra
)

# CMake package config
include(CMakePackageConfigHelpers)

write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/QuadraKernelConfigVersion.cmake"
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY AnyNewerVersion
)

configure_package_config_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/QuadraKernelConfig.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/QuadraKernelConfig.cmake"
    INSTALL_DESTINATION lib/cmake/QuadraKernel
)

install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/QuadraKernelConfig.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/QuadraKernelConfigVersion.cmake"
    DESTINATION lib/cmake/QuadraKernel
)

install(EXPORT QuadraKernelTargets
    FILE QuadraKernelTargets.cmake
    NAMESPACE Quadra::
    DESTINATION lib/cmake/QuadraKernel
)

# Uninstall target
if(NOT TARGET uninstall)
    configure_file(
        "${CMAKE_CURRENT_SOURCE_DIR}/cmake_uninstall.cmake.in"
        "${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake"
        IMMEDIATE @ONLY
    )
    
    add_custom_target(uninstall
        COMMAND ${CMAKE_COMMAND} -P ${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake
    )
endif()

# Print configuration summary
message(STATUS "")
message(STATUS "Quadra Kernel Configuration:")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Python bindings: ${BUILD_PYTHON_BINDINGS}")
message(STATUS "  Tests: ${BUILD_TESTS}")
message(STATUS "  Examples: ${BUILD_EXAMPLES}")
message(STATUS "  RTOS support: ${ENABLE_RTOS_SUPPORT}")
message(STATUS "  Hardware acceleration: ${ENABLE_HARDWARE_ACCEL}")
message(STATUS "")
