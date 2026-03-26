---
name: autosar-adaptive-platform
description: "Use when: Skill: AUTOSAR Adaptive Platform Development topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: AUTOSAR Adaptive Platform Development

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/autosar/adaptive-platform.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## When to Activate
- User asks about AUTOSAR Adaptive architecture or services
- User needs service-oriented architecture (SOA) guidance
- User requests ara::com service definition or communication patterns
- User is developing high-performance compute (HPC) applications
- User needs POSIX-based OS guidance for automotive
- User is working on machine learning deployment in vehicles

## Standards Compliance
- AUTOSAR Adaptive Platform R20-11 to R22-11
- ISO 26262 ASIL A/B (with partitioning for higher ASIL)
- MISRA C++:2014/2023 (coding guidelines)
- ASPICE Level 3
- ISO 21434 (cybersecurity for service interfaces)
- POSIX.1-2017 (OS compliance)

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Service discovery time | < 100 | ms |
| Inter-process communication | SOME/IP, DDS | protocol |
| Process startup time | 50-500 | ms |
| Service method latency | < 10 | ms |
| Event throughput | 1000-10000 | events/sec |
| Log message rate | 100-10000 | msgs/sec |
| Network management cycle | 100-200 | ms |
| Functional cluster count | 1-20 | clusters |

## Platform Architecture

```
+------------------------------------------------------------------+
|                    Application Layer (Functional Clusters)        |
|  +------------------+  +------------------+  +------------------+|
|  |  ADAS Cluster    |  |  Infotainment    |  |  Gateway Cluster ||
|  |  - Perception    |  |  - Navigation    |  |  - Routing        ||
|  |  - Planning      |  |  - Media         |  |  - Security       ||
|  +------------------+  +------------------+  +------------------+|
+------------------------------------------------------------------+
|                    Adaptive AUTOSAR Middleware (ara)              |
|  +------------+  +------------+  +------------+  +------------+  |
|  | ara::com   |  | ara::exec  |  | ara::log   |  | ara::nm    |  |
|  | (Comm Mgmt)|  | (Execution)|  | (Logging)  |  | (Network)  |  |
|  +------------+  +------------+  +------------+  +------------+  |
|  +------------+  +------------+  +------------+  +------------+  |
|  | ara::diag  |  | ara::pdu   |  | ara::sec   |  | ara::phm   |  |
|  | (Diag)     |  | (PDU Rout.)|  | (Security) |  | (Health)   |  |
|  +------------+  +------------+  +------------+  +------------+  |
+------------------------------------------------------------------+
|                    Transport Layer                                 |
|  +------------+  +------------+  +------------+  +------------+   |
|  | SOME/IP    |  | DoIP       |  | DDS        |  | MQTT       |   |
|  | (Service)  |  | (Diag)     |  | (Pub/Sub)  |  | (Cloud)    |   |
|  +------------+  +------------+  +------------+  +------------+   |
|  +------------+  +------------+  +------------+  +------------+   |
|  | TCP/IP     |  | UDP        |  | CAN/CAN FD |  | Ethernet   |   |
|  +------------+  +------------+  +------------+  +------------+   |
+------------------------------------------------------------------+
|                    Hardware Layer                                  |
|  +------------------+  +------------------+  +------------------+ |
|  |  Multi-core CPU  |  |  GPU/NPU         |  |  Storage (SSD)   | |
|  |  (ARM Cortex-A)  |  |  (ML Acceler.)   |  |  (UFS/eMMC)      | |
|  +------------------+  +------------------+  +------------------+ |
+------------------------------------------------------------------+
```

## Service-Oriented Architecture

### Service Definition (ara::com)

```cpp
// Service interface definition (.arxml or programmatic)
namespace ara::com::vehicle::dynamics {

// Data types for service interface
struct VehicleSpeed {
    float value_kmh;
    uint8_t quality;      // 0=Invalid, 1=Valid, 2=Degraded
    uint64_t timestamp_ns;
};

struct AccelerationRequest {
    float value_mps2;
    uint8_t source;       // 0=Driver, 1=ACC, 2=Autonomous
    uint32_t validity_flags;
};

// Service interface class
class VehicleMotionServiceInterface {
public:
    // Event for speed updates (publisher pattern)
    ara::com::Event<VehicleSpeed> SpeedUpdateEvent;

    // Event for acceleration commands
    ara::com::Event<AccelerationRequest> AccelerationRequestEvent;

    // Method: Set target speed (client-server pattern)
    ara::core::Result<void> SetTargetSpeed(float speed_kmh);

    // Method: Get current motion state
    ara::core::Result<VehicleSpeed> GetCurrentSpeed();

    // Field: Current driving mode (read/write state)
    ara::com::Field<DrivingMode> CurrentDrivingMode;

    virtual ~VehicleMotionServiceInterface() = default;
};

// Service proxy (client side - consumes service)
class VehicleMotionServiceProxy
    : public VehicleMotionServiceInterface {
public:
    // Factory method to find service instance
    static ara::core::Result<VehicleMotionServiceProxy> FindInstance(
        const ara::com::InstanceIdentifier& instance_id);

    // Subscribe to speed updates
    void SubscribeSpeedUpdate(
        std::function<void(const VehicleSpeed&)> callback,
        size_t max_queue_size = 10);

    // Unsubscribe from events
    void UnsubscribeSpeedUpdate();

    // Invoke methods asynchronously
    ara::core::Future<ara::core::Result<void>> SetTargetSpeedAsync(
        float speed_kmh,
        std::chrono::milliseconds timeout);

private:
    explicit VehicleMotionServiceProxy(
        const ara::com::InstanceIdentifier& instance_id);

    ara::com::ServiceProxyHandle proxy_handle_;
};

// Service skeleton (server side - provides service)
class VehicleMotionServiceSkeleton
    : public VehicleMotionServiceInterface {
public:
    explicit VehicleMotionServiceSkeleton(
        const ara::com::InstanceIdentifier& instance_id);

    // Offer service on the network
    void OfferService();

    // Stop offering service
    void StopOfferService();

    // Update event data (triggers notification to subscribers)
    void UpdateSpeed(const VehicleSpeed& speed);

    // Register method handlers
    void RegisterSetTargetSpeedHandler(
        std::function<ara::core::Result<void>(float)> handler);

private:
    ara::com::ServiceSkeletonHandle skeleton_handle_;
    ara::com::EventUpdateState speed_event_state_;
};

} // namespace ara::com::vehicle::dynamics
```

### Service Discovery and Subscription

```cpp
// Service consumer pattern
namespace oem::adas::perception {

class ObjectFusionController {
public:
    explicit ObjectFusionController(
        ara::log::Logger logger)
        : logger_(logger) {}

    ara::core::Result<void> Initialize() {
        // Find radar service instance
        auto radar_result =
            ara::com::RadarDetectionServiceProxy::FindInstance(
                ara::com::InstanceIdentifier("FrontRadar"));

        if (!radar_result.HasValue()) {
            logger_.LogError() << "Failed to find radar service: "
                               << radar_result.Error().Message();
            return radar_result.GetError();
        }
        radar_proxy_ = std::move(radar_result.Value());

        // Find camera service instance
        auto camera_result =
            ara::com::CameraDetectionServiceProxy::FindInstance(
                ara::com::InstanceIdentifier("FrontCamera"));

        if (!camera_result.HasValue()) {
            logger_.LogError() << "Failed to find camera service";
            return camera_result.GetError();
        }
        camera_proxy_ = std::move(camera_result.Value());

        // Subscribe to radar events
        radar_proxy_.SubscribeDetectedObjectsEvent(
            std::bind(&ObjectFusionController::OnRadarObjects,
                      this,
                      std::placeholders::_1),
            10);  // Queue up to 10 samples

        // Subscribe to camera events
        camera_proxy_.SubscribeDetectedObjectsEvent(
            std::bind(&ObjectFusionController::OnCameraObjects,
                      this,
                      std::placeholders::_1),
            10);

        logger_.LogInfo() << "Object fusion controller initialized";
        return ara::core::Result<void>::FromValue();
    }

private:
    void OnRadarObjects(const DetectedObjectList& objects) {
        logger_.LogDebug() << "Received " << objects.size()
                           << " objects from radar";
        FuseObjects(objects, SensorSource::RADAR);
    }

    void OnCameraObjects(const DetectedObjectList& objects) {
        logger_.LogDebug() << "Received " << objects.size()
                           << " objects from camera";
        FuseObjects(objects, SensorSource::CAMERA);
    }

    void FuseObjects(const DetectedObjectList& new_objects,
                     SensorSource source) {
        // Fusion algorithm implementation
        // Publish fused result via own service
    }

    ara::com::RadarDetectionServiceProxy radar_proxy_;
    ara::com::CameraDetectionServiceProxy camera_proxy_;
    ara::log::Logger logger_;
};

} // namespace oem::adas::perception
```

### Service Provider Implementation

```cpp
// Service provider pattern
namespace oem::sensors::radar {

class RadarDetectionService {
public:
    explicit RadarDetectionService(
        ara::log::Logger logger)
        : logger_(logger),
          skeleton_(ara::com::InstanceIdentifier("FrontRadar")),
          detected_objects_event_(
              skeleton_.GetEvent<DetectedObjectList>("DetectedObjects")) {}

    ara::core::Result<void> Initialize() {
        // Register method handlers
        skeleton_.RegisterCalibrateHandler(
            [this](const CalibrationParams& params) {
                return HandleCalibration(params);
            });

        skeleton_.RegisterGetStatusHandler(
            [this]() {
                return GetStatus();
            });

        // Initialize hardware
        return radar_hardware_.Initialize();
    }

    void Offer() {
        skeleton_.OfferService();
        logger_.LogInfo() << "Radar detection service offered";
    }

    void ProcessDetectionCycle() {
        // Acquire data from radar sensor
        auto detection_result = radar_hardware_.AcquireDetections();

        if (detection_result.HasValue()) {
            // Update event field - notifies all subscribers
            DetectedObjectList objects = detection_result.Value();
            detected_objects_event_.Update(objects);

            logger_.LogDebug() << "Published " << objects.size()
                               << " radar detections";
        }
    }

private:
    ara::core::Result<CalibrationResult> HandleCalibration(
        const CalibrationParams& params) {
        logger_.LogInfo() << "Calibration requested";

        // Perform calibration sequence
        auto result = radar_hardware_.Calibrate(params);

        if (result.HasValue()) {
            logger_.LogInfo() << "Calibration completed successfully";
        } else {
            logger_.LogError() << "Calibration failed";
        }

        return result;
    }

    ara::core::Result<SensorStatus> GetStatus() {
        return radar_hardware_.GetStatus();
    }

    ara::log::Logger logger_;
    ara::com::RadarDetectionServiceSkeleton skeleton_;
    ara::com::Event<DetectedObjectList> detected_objects_event_;
    RadarHardware radar_hardware_;
};

} // namespace oem::sensors::radar
```

## Execution Management (ara::exec)

### Process and State Management

```cpp
namespace oem::adas::camera_fusion {

class CameraFusionProcess {
public:
    explicit CameraFusionProcess(
        ara::log::Logger logger)
        : logger_(logger),
          exec_client_("CFUS") {}  // 4-char process ID

    ara::core::Result<void> Initialize() {
        // Report initial state
        exec_client_.ReportExecutionState(
            ara::exec::ExecutionState::kInitializing);

        // Initialize image processing pipeline
        auto result = image_processor_.Initialize();
        if (!result.HasValue()) {
            exec_client_.ReportExecutionState(
                ara::exec::ExecutionState::kInitializationFailed);
            return result.GetError();
        }

        // Subscribe to execution commands
        exec_client_.SubscribeExecutionState(
            [this](ara::exec::ExecutionState new_state) {
                OnExecutionStateChange(new_state);
            });

        logger_.LogInfo() << "Camera fusion process initialized";
        exec_client_.ReportExecutionState(
            ara::exec::ExecutionState::kRunning);
        return ara::core::Result<void>::FromValue();
    }

    void Run() {
        while (current_state_ == ara::exec::ExecutionState::kRunning) {
            // Process camera frames at target rate
            auto frame = camera_interface_.CaptureFrame();
            if (frame.HasValue()) {
                auto detections = image_processor_.DetectObjects(
                    frame.Value());
                PublishDetections(detections);
            }

            // Yield to allow other processes
            std::this_thread::sleep_for(std::chrono::milliseconds(33));
        }
    }

private:
    void OnExecutionStateChange(ara::exec::ExecutionState new_state) {
        logger_.LogInfo() << "Execution state change: "
                          << ExecutionStateToString(new_state);

        switch (new_state) {
            case ara::exec::ExecutionState::kRunning:
                current_state_ = new_state;
                break;

            case ara::exec::ExecutionState::kPause:
                current_state_ = new_state;
                image_processor_.Pause();
                break;

            case ara::exec::ExecutionState::kStop:
                current_state_ = new_state;
                image_processor_.Shutdown();
                break;

            default:
                break;
        }
    }

    void PublishDetections(const DetectedObjectList& detections) {
        // Publish via ara::com service
        detection_service_.UpdateDetections(detections);
    }

    ara::log::Logger logger_;
    ara::exec::ExecutionClient exec_client_;
    ara::exec::ExecutionState current_state_ =
        ara::exec::ExecutionState::kInitializing;
    ImageProcessor image_processor_;
    CameraInterface camera_interface_;
    DetectionService detection_service_;
};

// Process entry point (main function)
int main(int argc, char* argv[]) {
    // Initialize Adaptive Platform runtime
    ara::core::Initialize();

    // Create logger
    auto logger = ara::log::CreateLogger(
        "CFUS",
        "Camera Fusion Process",
        ara::log::LogLevel::kInfo);

    logger.LogInfo() << "Starting camera fusion process";

    // Create and run process
    CameraFusionProcess process(logger);
    auto result = process.Initialize();

    if (result.HasValue()) {
        process.Run();
    } else {
        logger.LogError() << "Failed to initialize process";
        return 1;
    }

    // Cleanup
    ara::core::Deinitialize();
    return 0;
}

} // namespace oem::adas::camera_fusion
```

## Logging (ara::log)

### Structured Logging

```cpp
namespace oem::adas {

class PerceptionModule {
public:
    PerceptionModule()
        : logger_(ara::log::CreateLogger(
              "PERC",                    // 4-char context ID
              "Perception Module",       // Full name
              ara::log::LogLevel::kInfo, // Default level
              " perception"              // Category for filtering
          )),
          detection_count_logger_(
              logger_.CreateChildLogger("detections")) {}

    void ProcessFrame(const CameraFrame& frame) {
        ara::log::TimestampedLogger ts_logger =
            logger_.WithTimestamp();

        ts_logger.LogDebug() << "Processing frame " << frame.sequence_number
                             << " (" << frame.width << "x" << frame.height
                             << ")";

        auto detections = RunInference(frame);

        // Log detection statistics
        detection_count_logger_.LogInfo()
            << "Detected " << detections.size() << " objects"
            << " [vehicles=" << CountByClass(detections, Class::VEHICLE)
            << ", pedestrians=" << CountByClass(detections, Class::PEDESTRIAN)
            << "]";

        // Log performance metrics
        ara::log::DurationLogger perf_logger =
            logger_.WithDuration(inference_time_ms_);
        perf_logger.LogDebug() << "Inference completed";
    }

    void ReportError(const ara::core::ErrorCode& error) {
        logger_.LogError()
            << "Perception error: " << error.Message()
            << " (domain: " << error.Domain().Name()
            << ", code: " << error.Code() << ")";
    }

private:
    ara::log::Logger logger_;
    ara::log::Logger detection_count_logger_;
    float inference_time_ms_ = 0.0f;
};

} // namespace oem::adas
```

### Log Sink Configuration

```yaml
# Log configuration manifest
log_configuration:
  contexts:
    - context_id: "PERC"
      name: "Perception Module"
      default_level: INFO
      sinks: ["console", "file", "ethernet"]

    - context_id: "FUSN"
      name: "Sensor Fusion"
      default_level: DEBUG
      sinks: ["file", "ethernet"]

    - context_id: "CTRL"
      name: "Motion Control"
      default_level: INFO
      sinks: ["console", "file", "can"]

  sinks:
    - sink_id: "console"
      type: CONSOLE
      format: "[{timestamp}] [{context}] [{level}] {message}"
      filter:
        min_level: INFO

    - sink_id: "file"
      type: FILE
      path: "/var/log/adas/"
      rotation:
        max_size_mb: 100
        max_files: 10
      format: JSON

    - sink_id: "ethernet"
      type: ETHERNET
      destination:
        ip: "192.168.1.100"
        port: 6801
      format: BINARY

    - sink_id: "can"
      type: CAN
      bus: "ADAS_CAN"
      message_id: 0x500
      format: TRUNCATED
```

## Network Management (ara::nm)

### Cluster Communication

```cpp
namespace oem::gateway {

class NetworkManager {
public:
    explicit NetworkManager(ara::log::Logger logger)
        : logger_(logger),
          nm_handle_("ADAS_CLUSTER") {}

    ara::core::Result<void> Initialize() {
        // Join network management cluster
        auto result = nm_handle_.JoinCluster({
            .cluster_name = "ADAS_CLUSTER",
            .node_id = "GatewayECU_001",
            .capabilities = {
                NetworkCapability::ROUTING,
                NetworkCapability::DIAGNOSTICS,
                NetworkCapability::SECURITY
            }
        });

        if (!result.HasValue()) {
            logger_.LogError() << "Failed to join cluster";
            return result.GetError();
        }

        // Subscribe to cluster state changes
        nm_handle_.SubscribeClusterState(
            [this](const ClusterState& state) {
                OnClusterStateChange(state);
            });

        // Subscribe to node join/leave events
        nm_handle_.SubscribeNodeEvents(
            [this](const NodeEvent& event) {
                OnNodeEvent(event);
            });

        logger_.LogInfo() << "Network manager initialized";
        return ara::core::Result<void>::FromValue();
    }

    void Start() {
        nm_handle_.StartCommunication();
        logger_.LogInfo() << "Network communication started";
    }

private:
    void OnClusterStateChange(const ClusterState& state) {
        logger_.LogInfo()
            << "Cluster state: " << ClusterStateToString(state.state)
            << " (nodes: " << state.active_nodes.size() << ")";

        // Update routing table based on cluster membership
        UpdateRoutingTable(state.active_nodes);
    }

    void OnNodeEvent(const NodeEvent& event) {
        if (event.type == NodeEventType::kJoined) {
            logger_.LogInfo() << "Node joined: " << event.node_id;
        } else if (event.type == NodeEventType::kLeft) {
            logger_.LogInfo() << "Node left: " << event.node_id;
        } else if (event.type == NodeEventType::kFailed) {
            logger_.LogWarning() << "Node failed: " << event.node_id;
            TriggerNodeRecovery(event.node_id);
        }
    }

    void UpdateRoutingTable(const std::vector<NodeInfo>& nodes) {
        // Update service routing based on available nodes
    }

    void TriggerNodeRecovery(const std::string& node_id) {
        // Attempt to recover failed node
    }

    ara::log::Logger logger_;
    ara::nm::NetworkManagerHandle nm_handle_;
};

} // namespace oem::gateway
```

## Manifest Configuration

### Application Manifest

```yaml
# camera_fusion_process.manifest.yaml
manifest_version: "2.1.0"
schema_version: "R22-11"

application:
  name: "CameraFusionProcess"
  uid: "oem.adas.perception.camera_fusion"
  version: "2.4.0"

execution:
  type: PROCESS
  run_command: "/opt/adas/camera_fusion_process"
  working_directory: "/opt/adas"
  user: "adas_service"
  group: "adas"

  scheduling:
    priority: 50  # 0-99, higher = more priority
    policy: SCHED_FIFO
    cpu_affinity: [0, 1]  # Pin to cores 0 and 1

  resources:
    memory_limit_mb: 512
    cpu_limit_percent: 80

  lifecycle:
    auto_start: true
    start_timeout_ms: 5000
    stop_timeout_ms: 2000
    restart_policy: ON_FAILURE
    max_restarts: 3

services:
  provided:
    - service_id: "oem.adas.DetectionService"
      instance_id: "FrontCamera"
      major_version: 2
      minor_version: 1
      transport: SOMEIP

  required:
    - service_id: "oem.sensors.CameraService"
      instance_id: "FrontCamera"
      major_version: "*"
      transport: SOMEIP

    - service_id: "oem.sensors.RadarService"
      instance_id: "FrontRadar"
      major_version: "*"
      transport: SOMEIP

communication:
  network_interfaces:
    - name: "adas_eth0"
      type: ETHERNET
      protocol: IPv4
      address: "192.168.10.10"
      netmask: "255.255.255.0"

logging:
  context_id: "CFUS"
  default_level: INFO
  sinks: ["file", "ethernet"]

security:
  capabilities:
    - "oem:capability:camera_access"
    - "oem:capability:network_communication"
  authentication:
    method: CERTIFICATE
    certificate_path: "/etc/ssl/camera_fusion.crt"
```

## Error Handling (ara::core)

### Result Types and Error Domains

```cpp
namespace oem::adas {

// Define custom error domain
enum class PerceptionErrc : ara::core::ErrorDomain::CodeType {
    kCameraNotReady = 1,
    kInvalidFrameFormat = 2,
    kInferenceTimeout = 3,
    kModelLoadingFailed = 4,
    kOutOfMemory = 5
};

class PerceptionErrorDomain : public ara::core::ErrorDomain {
public:
    using Errc = PerceptionErrc;

    constexpr PerceptionErrorDomain() noexcept
        : ErrorDomain(0x8000000000001001ULL) {}  // Unique domain ID

    char const* Name() const noexcept override {
        return "Perception";
    }

    char const* Message(CodeType code) const noexcept override {
        switch (static_cast<Errc>(code)) {
            case Errc::kCameraNotReady:
                return "Camera sensor not ready";
            case Errc::kInvalidFrameFormat:
                return "Invalid camera frame format";
            case Errc::kInferenceTimeout:
                return "Neural network inference timeout";
            case Errc::kModelLoadingFailed:
                return "Failed to load neural network model";
            case Errc::kOutOfMemory:
                return "Out of GPU memory";
            default:
                return "Unknown perception error";
        }
    }
};

constexpr PerceptionErrorDomain g_perceptionErrorDomain;

// Function returning Result type
ara::core::Result<DetectedObjectList> ProcessCameraFrame(
    const CameraFrame& frame,
    const NeuralNetworkModel& model) {

    // Validate input
    if (!frame.IsValid()) {
        return ara::core::Result<DetectedObjectList>::FromError(
            ara::core::ErrorCode(
                PerceptionErrc::kInvalidFrameFormat,
                g_perceptionErrorDomain));
    }

    // Run inference with timeout
    auto inference_result = model.RunInferenceAsync(
        frame,
        std::chrono::milliseconds(50));

    // Wait for result with timeout
    if (inference_result.WaitFor(
            std::chrono::milliseconds(50)) !=
        ara::core::FutureStatus::kReady) {
        return ara::core::Result<DetectedObjectList>::FromError(
            ara::core::ErrorCode(
                PerceptionErrc::kInferenceTimeout,
                g_perceptionErrorDomain));
    }

    // Get inference result
    auto detections = inference_result.Get();
    if (!detections.HasValue()) {
        return detections.GetError();
    }

    return ara::core::Result<DetectedObjectList>::FromValue(
        detections.Value());
}

// Usage with error handling
void PerceptionTask::Run() {
    auto frame = camera_.CaptureFrame();
    if (!frame.HasValue()) {
        logger_.LogError() << "Failed to capture frame";
        return;
    }

    auto result = ProcessCameraFrame(frame.Value(), model_);
    if (result.HasValue()) {
        PublishDetections(result.Value());
    } else {
        logger_.LogError()
            << "Frame processing failed: "
            << result.Error().Message()
            << " (code: " << result.Error().Code() << ")";

        // Report to health monitoring
        phm_client_.ReportError(result.Error());
    }
}

} // namespace oem::adas
```

## Health Monitoring (ara::phm)

### Process Health Reporting

```cpp
namespace oem::adas {

class HealthMonitor {
public:
    explicit HealthMonitor(ara::log::Logger logger)
        : logger_(logger),
          phm_client_("ADAS_HEALTH") {}

    ara::core::Result<void> Initialize() {
        // Register process for health monitoring
        return phm_client_.RegisterProcess({
            .process_id = "CameraFusion",
            .health_reporting_interval_ms = 1000,
            .expected_state = ara::exec::ExecutionState::kRunning
        });
    }

    void ReportHealth() {
        // Collect health metrics
        HealthMetrics metrics;
        metrics.cpu_usage_percent = GetCpuUsage();
        metrics.memory_usage_mb = GetMemoryUsage();
        metrics.processing_fps = GetProcessingFps();
        metrics.detection_count = GetDetectionCount();
        metrics.error_count = GetErrorCount();
        metrics.temperature_c = GetGpuTemperature();

        // Report to platform health manager
        phm_client_.ReportHealth(metrics);

        // Log if abnormal
        if (metrics.cpu_usage_percent > 90.0f) {
            logger_.LogWarning() << "High CPU usage: "
                                 << metrics.cpu_usage_percent << "%";
        }
        if (metrics.temperature_c > 85.0f) {
            logger_.LogError() << "GPU overheating: "
                               << metrics.temperature_c << "C";
        }
    }

    void ReportError(const ara::core::ErrorCode& error) {
        phm_client_.ReportError({
            .error_code = error,
            .severity = ErrorSeverity::kHigh,
            .timestamp = ara::core::Clock::GetTime()
        });
    }

private:
    ara::log::Logger logger_;
    ara::phm::PhmClient phm_client_;
};

} // namespace oem::adas
```

## Classic vs Adaptive Platform Comparison

| Aspect | Classic Platform | Adaptive Platform |
|--------|-----------------|-------------------|
| **Use Case** | Real-time control ECUs | High-performance compute |
| **Language** | C (MISRA C:2012) | C++ (MISRA C++:2023) |
| **OS** | OSEK/VDX, AUTOSAR OS | POSIX (Linux, QNX) |
| **Communication** | CAN, LIN, FlexRay | Ethernet, SOME/IP, DDS |
| **Architecture** | Signal-based | Service-oriented (SOA) |
| **Configuration** | ARXML | Manifest (YAML/JSON) |
| **Safety** | ASIL A-D (native) | ASIL A-B (with partitioning) |
| **Timing** | Deterministic (1-10ms) | Best-effort (10-100ms) |
| **Memory** | Static allocation | Dynamic allocation |
| **Examples** | Engine control, brake control, airbag | ADAS, infotainment, gateway |

## Approach

1. **Define Functional Clusters**
   - Identify high-level functions (perception, planning, control)
   - Map functions to processes and services
   - Define service interfaces (ara::com)

2. **Design Service Architecture**
   - Create service interface definitions
   - Define data types and enumerations
   - Specify QoS requirements

3. **Configure Execution Management**
   - Define process lifecycle states
   - Configure startup dependencies
   - Set scheduling priorities and CPU affinity

4. **Implement Communication**
   - Service discovery and subscription
   - Event publication patterns
   - Method call patterns (sync/async)

5. **Configure Network Management**
   - Define network clusters
   - Configure node capabilities
   - Set up routing rules

6. **Integrate Health Monitoring**
   - Register processes with PHM
   - Implement health reporting
   - Configure error escalation

## Deliverables

- Service interface definitions (IDL or header files)
- Application manifest files
- Process implementation (C++ source)
- ara::com service skeletons and proxies
- Network management configuration
- Health monitoring integration
- Log configuration and sinks
- Test specification (unit, integration, system)

## Related Context
- @context/skills/autosar/classic-platform.md
- @context/skills/autosar/rte-design.md
- @context/skills/adas/sensor-fusion.md
- @context/skills/adas/object-detection.md
- @context/skills/security/iso-21434-compliance.md
- @context/skills/safety/iso-26262-overview.md

## Tools Required
- Vector DaVinci Developer (Adaptive)
- EB Tresos Adaptive
- Qt Creator or CLion (IDE)
- Wireshark (SOME/IP analysis)
- dSPACE/ETAS HIL (system validation)
- Cppcheck/clang-tidy (static analysis)