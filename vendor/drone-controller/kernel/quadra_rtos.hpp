#ifndef QUADRA_RTOS_HPP
#define QUADRA_RTOS_HPP

/**
 * RTOS Compatibility Layer for Quadra Matrix SNN Kernel
 * 
 * Supports:
 * - FreeRTOS
 * - Zephyr RTOS
 * - NuttX
 * - QNX Neutrino
 * - VxWorks
 */

#include <cstdint>
#include <cstddef>

// RTOS detection
#if defined(__FREERTOS__)
    #define QUADRA_RTOS_FREERTOS
    #include "FreeRTOS.h"
    #include "task.h"
    #include "semphr.h"
    #include "queue.h"
#elif defined(__ZEPHYR__)
    #define QUADRA_RTOS_ZEPHYR
    #include <zephyr.h>
    #include <kernel.h>
#elif defined(__NUTTX__)
    #define QUADRA_RTOS_NUTTX
    #include <nuttx/config.h>
    #include <pthread.h>
    #include <semaphore.h>
#elif defined(__QNX__)
    #define QUADRA_RTOS_QNX
    #include <pthread.h>
    #include <semaphore.h>
#elif defined(__VXWORKS__)
    #define QUADRA_RTOS_VXWORKS
    #include <taskLib.h>
    #include <semLib.h>
#else
    #define QUADRA_RTOS_POSIX
    #include <pthread.h>
    #include <semaphore.h>
#endif

namespace quadra {
namespace rtos {

// ============================================================================
// Task Management
// ============================================================================

enum class TaskPriority {
    IDLE = 0,
    LOW = 1,
    NORMAL = 2,
    HIGH = 3,
    REALTIME = 4,
    CRITICAL = 5
};

class Task {
public:
    using TaskFunction = void (*)(void*);
    
    Task(const char* name, TaskFunction func, void* params, 
         TaskPriority priority, size_t stack_size = 4096);
    ~Task();
    
    bool start();
    bool stop();
    bool suspend();
    bool resume();
    
    TaskPriority get_priority() const;
    void set_priority(TaskPriority priority);
    
private:
#if defined(QUADRA_RTOS_FREERTOS)
    TaskHandle_t handle_;
#elif defined(QUADRA_RTOS_ZEPHYR)
    struct k_thread thread_;
    k_tid_t tid_;
#else
    pthread_t thread_;
#endif
    
    TaskFunction func_;
    void* params_;
    TaskPriority priority_;
    const char* name_;
    size_t stack_size_;
    bool running_;
};

// ============================================================================
// Synchronization Primitives
// ============================================================================

class Mutex {
public:
    Mutex();
    ~Mutex();
    
    bool lock(uint32_t timeout_ms = 0xFFFFFFFF);
    bool try_lock();
    void unlock();
    
private:
#if defined(QUADRA_RTOS_FREERTOS)
    SemaphoreHandle_t handle_;
#elif defined(QUADRA_RTOS_ZEPHYR)
    struct k_mutex mutex_;
#else
    pthread_mutex_t mutex_;
#endif
};

class Semaphore {
public:
    Semaphore(uint32_t initial_count = 0, uint32_t max_count = 1);
    ~Semaphore();
    
    bool wait(uint32_t timeout_ms = 0xFFFFFFFF);
    bool signal();
    uint32_t get_count() const;
    
private:
#if defined(QUADRA_RTOS_FREERTOS)
    SemaphoreHandle_t handle_;
#elif defined(QUADRA_RTOS_ZEPHYR)
    struct k_sem sem_;
#else
    sem_t sem_;
#endif
    uint32_t max_count_;
};

class Event {
public:
    Event();
    ~Event();
    
    bool wait(uint32_t timeout_ms = 0xFFFFFFFF);
    void set();
    void clear();
    
private:
#if defined(QUADRA_RTOS_FREERTOS)
    SemaphoreHandle_t handle_;
#elif defined(QUADRA_RTOS_ZEPHYR)
    struct k_event event_;
#else
    pthread_cond_t cond_;
    pthread_mutex_t mutex_;
#endif
    bool signaled_;
};

// ============================================================================
// Message Queues
// ============================================================================

template<typename T>
class MessageQueue {
public:
    MessageQueue(size_t capacity = 10);
    ~MessageQueue();
    
    bool send(const T& msg, uint32_t timeout_ms = 0xFFFFFFFF);
    bool receive(T& msg, uint32_t timeout_ms = 0xFFFFFFFF);
    size_t size() const;
    bool is_full() const;
    bool is_empty() const;
    
private:
#if defined(QUADRA_RTOS_FREERTOS)
    QueueHandle_t handle_;
#elif defined(QUADRA_RTOS_ZEPHYR)
    struct k_msgq msgq_;
    char* buffer_;
#else
    // Custom implementation for POSIX
    T* buffer_;
    size_t head_;
    size_t tail_;
    size_t count_;
    pthread_mutex_t mutex_;
    pthread_cond_t cond_not_full_;
    pthread_cond_t cond_not_empty_;
#endif
    size_t capacity_;
};

// ============================================================================
// Memory Management
// ============================================================================

class MemoryPool {
public:
    MemoryPool(size_t block_size, size_t num_blocks);
    ~MemoryPool();
    
    void* allocate(uint32_t timeout_ms = 0xFFFFFFFF);
    void free(void* ptr);
    
    size_t available() const;
    size_t total() const;
    
private:
#if defined(QUADRA_RTOS_FREERTOS)
    // Custom pool implementation
#elif defined(QUADRA_RTOS_ZEPHYR)
    struct k_mem_pool pool_;
#else
    // Custom pool implementation
#endif
    void* memory_;
    size_t block_size_;
    size_t num_blocks_;
    void** free_list_;
    Mutex mutex_;
};

// ============================================================================
// Timer Management
// ============================================================================

class Timer {
public:
    using TimerCallback = void (*)(void*);
    
    enum class Type {
        ONE_SHOT,
        PERIODIC
    };
    
    Timer(const char* name, TimerCallback callback, void* params, Type type);
    ~Timer();
    
    bool start(uint32_t period_ms);
    bool stop();
    bool reset();
    bool is_active() const;
    
private:
#if defined(QUADRA_RTOS_FREERTOS)
    TimerHandle_t handle_;
#elif defined(QUADRA_RTOS_ZEPHYR)
    struct k_timer timer_;
#else
    timer_t timer_id_;
#endif
    
    TimerCallback callback_;
    void* params_;
    Type type_;
    const char* name_;
};

// ============================================================================
// Interrupt Management (for bare-metal/RTOS)
// ============================================================================

class InterruptLock {
public:
    InterruptLock();
    ~InterruptLock();
    
private:
#if defined(QUADRA_RTOS_FREERTOS)
    UBaseType_t saved_interrupt_status_;
#elif defined(QUADRA_RTOS_ZEPHYR)
    unsigned int key_;
#else
    // No-op for POSIX
#endif
};

// ============================================================================
// System Information
// ============================================================================

class System {
public:
    static uint64_t get_tick_count();
    static uint32_t get_tick_rate_hz();
    static uint64_t get_time_us();
    
    static void delay_ms(uint32_t ms);
    static void delay_us(uint32_t us);
    
    static size_t get_free_heap_size();
    static size_t get_min_free_heap_size();
    
    static const char* get_rtos_name();
    static const char* get_rtos_version();
};

// ============================================================================
// Drone-Specific RTOS Integration
// ============================================================================

/**
 * @brief High-frequency control loop for drone systems
 * 
 * Runs at 1kHz for real-time flight control
 */
class DroneControlTask : public Task {
public:
    DroneControlTask(void* snn_kernel);
    ~DroneControlTask();
    
    bool initialize();
    void set_control_frequency(uint32_t hz);
    
private:
    static void control_loop(void* params);
    
    void* snn_kernel_;
    uint32_t control_period_ms_;
    Timer* control_timer_;
};

/**
 * @brief Sensor data acquisition task
 * 
 * Reads IMU, GPS, barometer at high frequency
 */
class SensorTask : public Task {
public:
    SensorTask();
    ~SensorTask();
    
    bool initialize();
    void register_sensor_callback(void (*callback)(const void* data));
    
private:
    static void sensor_loop(void* params);
    
    MessageQueue<float>* imu_queue_;
    MessageQueue<float>* gps_queue_;
};

/**
 * @brief Telemetry and logging task (lower priority)
 */
class TelemetryTask : public Task {
public:
    TelemetryTask();
    ~TelemetryTask();
    
    bool initialize();
    void log_data(const char* data, size_t len);
    
private:
    static void telemetry_loop(void* params);
    
    MessageQueue<char*>* log_queue_;
};

} // namespace rtos
} // namespace quadra

// ============================================================================
// Convenience Macros
// ============================================================================

#define QUADRA_TASK_PRIORITY(level) quadra::rtos::TaskPriority::level
#define QUADRA_ENTER_CRITICAL() quadra::rtos::InterruptLock __lock
#define QUADRA_DELAY_MS(ms) quadra::rtos::System::delay_ms(ms)
#define QUADRA_DELAY_US(us) quadra::rtos::System::delay_us(us)

#endif // QUADRA_RTOS_HPP
