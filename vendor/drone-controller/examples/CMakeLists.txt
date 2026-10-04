cmake_minimum_required(VERSION 3.15)

# Find parent Quadra Kernel library
find_package(QuadraKernel QUIET)

if(NOT QuadraKernel_FOUND)
    # If not installed, use local build
    set(QUADRA_KERNEL_INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/..)
    set(QUADRA_KERNEL_LIB quadra_kernel)
endif()

# C++ examples
add_executable(basic_cpp_example basic_cpp_example.cpp)
target_link_libraries(basic_cpp_example PRIVATE ${QUADRA_KERNEL_LIB})
target_include_directories(basic_cpp_example PRIVATE ${QUADRA_KERNEL_INCLUDE_DIR})

# Install examples
install(TARGETS basic_cpp_example
    RUNTIME DESTINATION bin/examples
)

install(FILES
    basic_usage.py
    drone_controller.py
    DESTINATION share/quadra/examples
)
