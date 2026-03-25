# BSW Configuration Output: EngineControl ECU

## BSW Configuration Execution Summary

**Tool**: `autosar-bsw-config`
**Version**: 1.2.0 (AUTOSAR R22-11 BSW configurator compliant)
**Execution Time**: 3.4 seconds
**Status**: SUCCESS

---

## BSW Module Configuration

### Overview

| Module | Version | Config Status | Memory Usage |
|--------|---------|---------------|--------------|
| Can | 4.3.0 | Complete | ROM: 4.2 KB, RAM: 512 B |
| CanIf | 5.2.0 | Complete | ROM: 3.8 KB, RAM: 256 B |
| Com | 6.0.0 | Complete | ROM: 5.1 KB, RAM: 1.2 KB |
| Dem | 3.1.0 | Complete | ROM: 8.4 KB, RAM: 2.0 KB |
| NvM | 2.1.0 | Complete | ROM: 6.2 KB, RAM: 512 B |
| WdgM | 1.0.0 | Complete | ROM: 1.2 KB, RAM: 128 B |
| Os | 4.0.0 | Complete | ROM: 3.5 KB, RAM: 1.5 KB |
| **Total BSW** | - | - | **ROM: 32.4 KB, RAM: 6.1 KB** |

---

## Can Module Configuration

### CanGeneral

```yaml
CanConfigSet:
  CanDevErrorDetect: STD_ON
  CanVersionInfoApi: STD_OFF
  CanTimeoutMonitoring: STD_ON
  CanMainFunctionPeriod: 0.001  # 1ms
  CanController:
    - CanControllerId: 0
      CanControllerName: "CanController0"
      CanControllerActivation: TRUE
      CanControllerBaudRate: 500  # 500 kbps
      CanControllerSeg1: 13
      CanControllerSeg2: 2
      CanControllerPropSeg: 1
      CanControllerSyncJumpWidth: 1
      CanRxProcessing: FULL
      CanTxProcessing: FULL
      CanWakeUpSupport: FALSE
```

### CanHardwareObject

```yaml
CanHardwareObject:
  # RX Message Objects
  - CanHandleType: CAN_ARC_TYPE_RX
    CanIdValue: 0x100
    CanIdMask: 0x7FF
    CanObjectId: 0
    CanObjectType: CAN_OBJECT_TYPE_RECEIVE
    CanFilterMask: 0x7FF
    CanFilterType: CAN_FILTER_TYPE_RANGE
    SoftwareFilterType: CAN_SOFT_FILTER_OFF
    CanIdType: CAN_ID_TYPE_STANDARD

  - CanHandleType: CAN_ARC_TYPE_RX
    CanIdValue: 0x200
    CanIdMask: 0x7FF
    CanObjectId: 1
    CanObjectType: CAN_OBJECT_TYPE_RECEIVE
    CanFilterMask: 0x7FF
    CanFilterType: CAN_FILTER_TYPE_RANGE
    SoftwareFilterType: CAN_SOFT_FILTER_OFF
    CanIdType: CAN_ID_TYPE_STANDARD

  # TX Message Objects
  - CanHandleType: CAN_ARC_TYPE_TX
    CanIdValue: 0x100
    CanObjectId: 2
    CanObjectType: CAN_OBJECT_TYPE_TRANSMIT
    CanIdType: CAN_ID_TYPE_STANDARD

  - CanHandleType: CAN_ARC_TYPE_TX
    CanIdValue: 0x200
    CanObjectId: 3
    CanObjectType: CAN_OBJECT_TYPE_TRANSMIT
    CanIdType: CAN_ID_TYPE_STANDARD
```

### CanBufferDefinition

```yaml
CanBufferDefinition:
  # RX Buffers
  - CanBufferType: CAN_RX
    CanBufferSize: 16  # 16 messages
    CanBufferId: 0
    CanAssociatedToObject: 0

  - CanBufferType: CAN_RX
    CanBufferSize: 8
    CanBufferId: 1
    CanAssociatedToObject: 1

  # TX Buffers
  - CanBufferType: CAN_TX
    CanBufferSize: 8
    CanBufferId: 2
    CanAssociatedToObject: 2

  - CanBufferType: CAN_TX
    CanBufferSize: 8
    CanBufferId: 3
    CanAssociatedToObject: 3
```

---

## CanIf Module Configuration

### CanIfGeneral

```yaml
CanIfConfigSet:
  CanIfDevErrorDetect: STD_ON
  CanIfVersionInfoApi: STD_OFF
  CanIfDynTxBufferSupport: FALSE
  CanIfReadRxPduDataApi: STD_ON
  CanIfSetDynamicTxIdApi: STD_OFF
  CanIfTransmitCancellation: STD_OFF
```

### CanIfBufferCfg

```yaml
CanIfBufferCfg:
  - CanIfBufferId: 0
    CanIfBufferSize: 16
    CanIfBufferType: CANIF_BUFFER_TYPE_RX
    CanIfAssociatedWithCanController: 0

  - CanIfBufferId: 1
    CanIfBufferSize: 8
    CanIfBufferType: CANIF_BUFFER_TYPE_TX
    CanIfAssociatedWithCanController: 0
```

### CanIfRxPduCfg

```yaml
CanIfRxPduCfg:
  # BMS_Status (0x200) - Received from vehicle CAN
  - CanIfRxPduId: 0
    CanIfPduId: 0
    LowerCanId: 0x200
    UpperCanId: 0x200
    CanIfPduType: CANIF_PDU_TYPE_STATIC
    CanIfUserRxIndication: Com_RxIndication
    CanIfSoftwareFilterType: CANIF_SOFTFILTER_TYPE_NONE
    CanIfDlc: 8

  # VehicleSpeed (0x100) - Received from vehicle CAN
  - CanIfRxPduId: 1
    CanIfPduId: 1
    LowerCanId: 0x100
    UpperCanId: 0x100
    CanIfPduType: CANIF_PDU_TYPE_STATIC
    CanIfUserRxIndication: Com_RxIndication
    CanIfSoftwareFilterType: CANIF_SOFTFILTER_TYPE_NONE
    CanIfDlc: 8

  # DiagnosticRequest - Received via UDS
  - CanIfRxPduId: 2
    CanIfPduId: 2
    LowerCanId: 0x7DF
    UpperCanId: 0x7DF
    CanIfPduType: CANIF_PDU_TYPE_STATIC
    CanIfUserRxIndication: Dcm_RxIndication
    CanIfSoftwareFilterType: CANIF_SOFTFILTER_TYPE_NONE
    CanIfDlc: 8
```

### CanIfTxPduCfg

```yaml
CanIfTxPduCfg:
  # EngineStatus (0x200) - Transmitted to vehicle CAN
  - CanIfTxPduId: 0
    CanIfPduId: 0
    CanId: 0x200
    CanIfPduType: CANIF_PDU_TYPE_STATIC
    CanIfUserTxConfirmation: Com_TxConfirmation
    CanIfDlc: 8
    CanIfTxPduCanIdType: STANDARD

  # BMS_Status (0x100) - Transmitted to vehicle CAN
  - CanIfTxPduId: 1
    CanIfPduId: 1
    CanId: 0x100
    CanIfPduType: CANIF_PDU_TYPE_STATIC
    CanIfUserTxConfirmation: Com_TxConfirmation
    CanIfDlc: 8
    CanIfTxPduCanIdType: STANDARD

  # DiagnosticResponse - Transmitted via UDS
  - CanIfTxPduId: 2
    CanIfPduId: 2
    CanId: 0x7E8
    CanIfPduType: CANIF_PDU_TYPE_STATIC
    CanIfUserTxConfirmation: Dcm_TxConfirmation
    CanIfDlc: 8
    CanIfTxPduCanIdType: STANDARD
```

---

## Com Module Configuration

### ComGeneral

```yaml
ComConfig:
  ComDevErrorDetect: STD_ON
  ComVersionInfoApi: STD_OFF
  ComMainFunctionPeriod: 0.001  # 1ms
  ComSupportExtendedReceiveSignal: STD_ON
  ComSignalEndianess: COM_OPPORTUNE_ENDIANESS
  ComSignalInitValue: STD_ON
  ComTimeoutMonitoring: STD_ON
  ComIpdUMode: FALSE
  ComNBytes: 64
  ComNMessages: 32
```

### ComIPdu

```yaml
ComIPdu:
  # PDU_BMS_Status (TX, 100ms cyclic)
  - ComIPduId: 0
    ComIPduSignalGroupRef: "BMS_Status_SigGroup"
    ComIPduDirection: SEND
    ComIPduCallout: ComIpduCallout_BMS_Status
    ComTxIPdu:
      ComTxIPduMinimalDelay: 0
      ComTxIPduDeadline: 120  # 120ms deadline
      ComTxMode:
        ComTxModeMode: DIRECT
        ComTxModeNumberOfRepetitions: 0
        ComTxModeRepetitionPeriod: 0
        ComTxModeTimeOffset: 0
        ComTxModeTimePeriod: 100  # 100ms cyclic

  # PDU_VehicleSpeed (RX, timeout monitored)
  - ComIPduId: 1
    ComIPduSignalGroupRef: "VehicleSpeed_SigGroup"
    ComIPduDirection: RECEIVE
    ComIPduCallout: ComIpduCallout_VehicleSpeed
    ComRxIPdu:
      ComIPduSignalGroupRef: "VehicleSpeed_SigGroup"
      ComTimeout: 50  # 50ms timeout
      ComTimeoutNotification: Com_VehicleSpeed_Timeout

  # PDU_EngineStatus (TX, 100ms cyclic)
  - ComIPduId: 2
    ComIPduSignalGroupRef: "EngineStatus_SigGroup"
    ComIPduDirection: SEND
    ComIPduCallout: ComIpduCallout_EngineStatus
    ComTxIPdu:
      ComTxIPduMinimalDelay: 0
      ComTxIPduDeadline: 120
      ComTxMode:
        ComTxModeMode: DIRECT
        ComTxModeNumberOfRepetitions: 0
        ComTxModeRepetitionPeriod: 0
        ComTxModeTimeOffset: 0
        ComTxModeTimePeriod: 100  # 100ms cyclic
```

### ComSignal

```yaml
ComSignal:
  # EngineStatus signals (TX)
  - ComSignalId: 0
    ComSignalName: "EngineStatus_RPM"
    ComSignalType: UINT16
    ComBitPosition: 0
    ComBitSize: 16
    ComSignalEndianess: COM_OPPORTUNE_ENDIANESS
    ComSignalInitValue: "Com_EngineStatus_RPM_Init"
    ComSignalArcUseUpdateBit: FALSE
    ComSignalHandle: "ComEngineStatusRpm"

  - ComSignalId: 1
    ComSignalName: "EngineStatus_Load"
    ComSignalType: UINT8
    ComBitPosition: 16
    ComBitSize: 8
    ComSignalEndianess: COM_OPPORTUNE_ENDIANESS
    ComSignalInitValue: "Com_EngineStatus_Load_Init"
    ComSignalArcUseUpdateBit: FALSE
    ComSignalHandle: "ComEngineStatusLoad"

  - ComSignalId: 2
    ComSignalName: "EngineStatus_Torque"
    ComSignalType: UINT16
    ComBitPosition: 24
    ComBitSize: 16
    ComSignalEndianess: COM_OPPORTUNE_ENDIANESS
    ComSignalInitValue: "Com_EngineStatus_Torque_Init"
    ComSignalArcUseUpdateBit: FALSE
    ComSignalHandle: "ComEngineStatusTorque"

  - ComSignalId: 3
    ComSignalName: "EngineStatus_Temp"
    ComSignalType: UINT8
    ComBitPosition: 40
    ComBitSize: 8
    ComSignalEndianess: COM_OPPORTUNE_ENDIANESS
    ComSignalInitValue: "Com_EngineStatus_Temp_Init"
    ComSignalArcUseUpdateBit: FALSE
    ComSignalHandle: "ComEngineStatusTemp"

  # VehicleSpeed signals (RX)
  - ComSignalId: 4
    ComSignalName: "VehicleSpeed_Value"
    ComSignalType: UINT16
    ComBitPosition: 0
    ComBitSize: 16
    ComSignalEndianess: COM_OPPORTUNE_ENDIANESS
    ComSignalInitValue: "Com_VehicleSpeed_Value_Init"
    ComSignalArcUseUpdateBit: FALSE
    ComSignalHandle: "ComVehicleSpeedValue"

  - ComSignalId: 5
    ComSignalName: "VehicleSpeed_Quality"
    ComSignalType: UINT8
    ComBitPosition: 16
    ComBitSize: 8
    ComSignalEndianess: COM_OPPORTUNE_ENDIANESS
    ComSignalInitValue: "Com_VehicleSpeed_Quality_Init"
    ComSignalArcUseUpdateBit: FALSE
    ComSignalHandle: "ComVehicleSpeedQuality"
```

### ComSignalInitValue

```yaml
ComSignalInitValue:
  - ComSignalInitValueName: "Com_EngineStatus_RPM_Init"
    ComSignalInitValueDef: 0

  - ComSignalInitValueName: "Com_EngineStatus_Load_Init"
    ComSignalInitValueDef: 0

  - ComSignalInitValueName: "Com_EngineStatus_Torque_Init"
    ComSignalInitValueDef: 0

  - ComSignalInitValueName: "Com_EngineStatus_Temp_Init"
    ComSignalInitValueDef: 25

  - ComSignalInitValueName: "Com_VehicleSpeed_Value_Init"
    ComSignalInitValueDef: 0

  - ComSignalInitValueName: "Com_VehicleSpeed_Quality_Init"
    ComSignalInitValueDef: 0  # Invalid until first message received
```

### ComTimeout

```yaml
ComTimeout:
  - ComTimeoutNotification: "Com_VehicleSpeed_Timeout"
    ComTimeoutTime: 50  # 50ms

ComTimeoutNotification:
  - ComTimeoutNotificationName: "Com_VehicleSpeed_Timeout"
    ComTimeoutNotificationType: COM_TIMEOUT_NOTIFICATION_TYPE_IMMEDIATE
```

---

## Dem Module Configuration

### DemGeneral

```yaml
DemCfg:
  DemDevErrorDetect: STD_ON
  DemVersionInfoApi: STD_OFF
  DemMainFunctionPeriod: 0.01  # 10ms
  DemGeneralProps: DEM_OBD_SUPPORT_ON
  DemSizeOfMemorySection: 100  # Maximum 100 DTCs
  DemMaxPreStoredFreezeFrames: 10
  DemMaxEventMirrored: 50
  DemDTCFormat: DEM_DTC_FORMAT_ISO14229_1
  DemPrimaryMemorySize: 4096  # 4KB primary memory
  DemMirrorMemorySize: 1024   # 1KB mirror memory
```

### DemEventParameter

```yaml
DemEventParameter:
  # Overcurrent fault
  - DemEventId: 0
    DemEventName: "Dem_Event_Overcurrent"
    DemDTCFormat: ISO14229_1
    DemDTC: 0xBMS042
    DemDTCAgingCycle: 10
    DemDTCOrigin: DEM_DTC_ORIGIN_PRIMARY_MEMORY
    DemFaultDetectionCounter: 0
    DemEventDestination:
      - DEM_DESTINATION_PRIMARY_MEMORY
      - DEM_DESTINATION_MIRROR_MEMORY
    DemEventData:
      - DemEventDataClass: CLASS_FROZEN_FRAME
        DemEventDataSize: 64
      - DemEventDataClass: CLASS_EXTENDED_DATA
        DemEventDataSize: 16
    DemOperationCycle: DEM_OBD_DRIVE_CYCLE

  # Cell overvoltage fault
  - DemEventId: 1
    DemEventName: "Dem_Event_CellOvervoltage"
    DemDTC: 0xBMS043
    DemDTCAgingCycle: 10
    DemDTCOrigin: DEM_DTC_ORIGIN_PRIMARY_MEMORY
    DemEventDestination:
      - DEM_DESTINATION_PRIMARY_MEMORY
      - DEM_DESTINATION_MIRROR_MEMORY

  # Cell undervoltage fault
  - DemEventId: 2
    DemEventName: "Dem_Event_CellUndervoltage"
    DemDTC: 0xBMS044
    DemDTCAgingCycle: 10
    DemDTCOrigin: DEM_DTC_ORIGIN_PRIMARY_MEMORY
    DemEventDestination:
      - DEM_DESTINATION_PRIMARY_MEMORY
      - DEM_DESTINATION_MIRROR_MEMORY

  # Sensor plausibility fault
  - DemEventId: 3
    DemEventName: "Dem_Event_SensorPlausibility"
    DemDTC: 0xBMS045
    DemDTCAgingCycle: 10
    DemDTCOrigin: DEM_DTC_ORIGIN_PRIMARY_MEMORY
    DemEventDestination:
      - DEM_DESTINATION_PRIMARY_MEMORY

  # Communication timeout
  - DemEventId: 4
    DemEventName: "Dem_Event_ComTimeout"
    DemDTC: 0xBMS046
    DemDTCAgingCycle: 5
    DemDTCOrigin: DEM_DTC_ORIGIN_PRIMARY_MEMORY
    DemEventDestination:
      - DEM_DESTINATION_PRIMARY_MEMORY
```

### DemDataSetIdentifier

```yaml
DemDataSetIdentifier:
  - DemDataSetName: "FreezeFrame_Primary"
    DemDataSetRecordSize: 64
    DemDataElementClass:
      - DEM_DATA_ELEMENT_CLASS_VEHICLE_SPEED
      - DEM_DATA_ELEMENT_CLASS_ENGINE_SPEED
      - DEM_DATA_ELEMENT_CLASS_COOLANT_TEMP
      - DEM_DATA_ELEMENT_CLASS_THROTTLE_POSITION

  - DemDataSetName: "ExtendedData_Overcurrent"
    DemDataSetRecordSize: 16
    DemDataElementClass:
      - DEM_DATA_ELEMENT_CLASS_PACK_CURRENT
      - DEM_DATA_ELEMENT_CLASS_PACK_VOLTAGE
      - DEM_DATA_ELEMENT_CLASS_FAULT_COUNTER
```

---

## NvM Module Configuration

### NvMGeneral

```yaml
NvM:
  NvmDevErrorDetect: STD_ON
  NvmVersionInfoApi: STD_OFF
  NvmMainFunctionPeriod: 0.01  # 10ms
  NvmSizeRamSection: 2048  # 2KB RAM section
  NvmNumberOfRamBlocks: 16
  NvmNumberOfRomBlocks: 4
  NvmNumberStandardRamBlocks: 12
  NvmNumberStandardRomBlocks: 4
```

### NvMRamBlockDescriptor

```yaml
NvMRamBlockDescriptor:
  # Calibration data block
  - NvMBlockDescriptorName: "NvM_CalibrationData"
    NvMRamBlockDataAddress: "&NvM_CalibrationData_RAM"
    NvMROMBlockDataAddress: "&NvM_CalibrationData_ROM"
    NvMNvmBlockType: NATIVE_BLOCK
    NvMSelectableBlockType: SELECTABLE_NONE
    NvmBlockManagementType: NATIVE
    NvMCrcType: CRC_32
    NvmCalcRamBlockCrc: TRUE
    NvmResistantToChangedSw: TRUE
    NvMWriteToRomAtInit: FALSE
    NvMReadRamBlockFromRomAtInit: TRUE
    NvMWriteOnlyOnce: FALSE
    NvMBlockBasePriority: 10

  # Vehicle configuration data
  - NvMBlockDescriptorName: "NvM_VehicleConfig"
    NvMRamBlockDataAddress: "&NvM_VehicleConfig_RAM"
    NvMROMBlockDataAddress: "&NvM_VehicleConfig_ROM"
    NvMNvmBlockType: NATIVE_BLOCK
    NvmBlockManagementType: NATIVE
    NvMCrcType: CRC_32
    NvmCalcRamBlockCrc: TRUE
    NvmResistantToChangedSw: TRUE
    NvMWriteToRomAtInit: FALSE
    NvMReadRamBlockFromRomAtInit: TRUE
    NvMBlockBasePriority: 20

  # DTC storage
  - NvMBlockDescriptorName: "NvM_DtcStorage"
    NvMRamBlockDataAddress: "&NvM_DtcStorage_RAM"
    NvMROMBlockDataAddress: "&NvM_DtcStorage_ROM"
    NvMNvmBlockType: NATIVE_BLOCK
    NvmBlockManagementType: NATIVE
    NvMCrcType: NONE
    NvmCalcRamBlockCrc: FALSE
    NvmResistantToChangedSw: TRUE
    NvMWriteToRomAtInit: FALSE
    NvMReadRamBlockFromRomAtInit: TRUE
    NvMBlockBasePriority: 100  # Highest priority

  # Fault history
  - NvMBlockDescriptorName: "NvM_FaultHistory"
    NvMRamBlockDataAddress: "&NvM_FaultHistory_RAM"
    NvMROMBlockDataAddress: "&NvM_FaultHistory_ROM"
    NvMNvmBlockType: NATIVE_BLOCK
    NvmBlockManagementType: NATIVE
    NvMCrcType: CRC_16
    NvmCalcRamBlockCrc: TRUE
    NvmResistantToChangedSw: FALSE
    NvMWriteToRomAtInit: FALSE
    NvMReadRamBlockFromRomAtInit: TRUE
    NvMBlockBasePriority: 50
```

---

## WdgM Module Configuration

### WdgMGeneral

```yaml
WdgM:
  WdgMDevErrorDetect: STD_ON
  WdgMVersionInfoApi: STD_OFF
  WdgMMainFunctionPeriod: 0.01  # 10ms
  WdgMNumberOfSupervisedPaths: 3
  WdgMNumberOfCheckpointPaths: 0
  WdgMTimeResolution: 0.001  # 1ms
  WdgMWatchdogDriver: "Wdg_0"
```

### WdgMSupervisedPath

```yaml
WdgMSupervisedPath:
  # RTE main function supervision
  - WdgMSupervisedPathName: "WdgM_RtePath"
    WdgMExpectedDurationMin: 0.008  # Min 8ms
    WdgMExpectedDurationMax: 0.012  # Max 12ms
    WdgMDeadlineMax: 0.015  # Max 15ms
    WdgMSupervisedPathRef:
      - &Rte_MainFunction

  # Application task supervision
  - WdgMSupervisedPathName: "WdgM_ApplicationPath"
    WdgMExpectedDurationMin: 0.008
    WdgMExpectedDurationMax: 0.012
    WdgMDeadlineMax: 0.015
    WdgMSupervisedPathRef:
      - &Task_Cyclic_10ms
      - &Task_Cyclic_100ms

  # Communication supervision
  - WdgMSupervisedPathName: "WdgM_CommPath"
    WdgMExpectedDurationMin: 0.0005  # Min 0.5ms
    WdgMExpectedDurationMax: 0.002  # Max 2ms
    WdgMDeadlineMax: 0.005  # Max 5ms
    WdgMSupervisedPathRef:
      - &Can_MainFunction
      - &Com_MainFunction
```

### WdgMMode

```yaml
WdgMMode:
  - WdgMModeName: "WdgM_NormalMode"
    WdgMModeId: 0
    WdgMModeFailureReaction: RESTART
    WdgMModeCheckpointCount: 0
```

---

## Os Module Configuration

### OsOS

```yaml
OsOS:
  OsSystemCounterName: "OsCounter"
  OsCounterMaxAllowedValue: 60000  # 60 seconds at 1ms tick
  OsCounterTicksPerBase: 1000      # 1ms base
  OsCounterMinCycle: 1
  OsSchedulePolicy: FULL_PREEMPTIVE
  OsStackSize: 2048  # Default stack size
  OsInterruptStackSize: 512
  OsProtectMemory: TRUE
  OsProtectionHook: TRUE
  OsShutdownHook: TRUE
  OsStartupHook: TRUE
  OsErrorHook: TRUE
```

### OsTask

```yaml
OsTask:
  # 10ms cyclic task (ASIL-B)
  - OsTaskName: "Task_Cyclic_10ms"
    OsTaskActivations: 1
    OsTaskAutostart: TRUE
    OsTaskPriority: 80
    OsTaskSchedule: FULL
    OsTaskStackSize: 1024
    OsTaskAccessingApplication: "EngineControl_App"
    OsTaskEvent: NULL
    OsTaskAlarm: "Alarm_Cyclic_10ms"
    OsTaskTrusted: FALSE

  # 100ms cyclic task (ASIL-B)
  - OsTaskName: "Task_Cyclic_100ms"
    OsTaskActivations: 1
    OsTaskAutostart: TRUE
    OsTaskPriority: 60
    OsTaskSchedule: FULL
    OsTaskStackSize: 1024
    OsTaskAccessingApplication: "EngineControl_App"
    OsTaskEvent: NULL
    OsTaskAlarm: "Alarm_Cyclic_100ms"
    OsTaskTrusted: FALSE

  # Event-triggered diagnostic task (QM)
  - OsTaskName: "Task_Event_Diag"
    OsTaskActivations: 1
    OsTaskAutostart: FALSE  # Event-triggered
    OsTaskPriority: 80
    OsTaskSchedule: FULL
    OsTaskStackSize: 1024
    OsTaskAccessingApplication: "EngineControl_App"
    OsTaskEvent: "Event_DiagnosticRequest"
    OsTaskAlarm: NULL
    OsTaskTrusted: FALSE

  # Background task (QM)
  - OsTaskName: "Task_Background"
    OsTaskActivations: 1
    OsTaskAutostart: TRUE
    OsTaskPriority: 10
    OsTaskSchedule: FULL
    OsTaskStackSize: 512
    OsTaskAccessingApplication: "EngineControl_App"
    OsTaskEvent: NULL
    OsTaskAlarm: NULL
    OsTaskTrusted: FALSE
```

### OsAlarm

```yaml
OsAlarm:
  # 10ms cyclic alarm
  - OsAlarmName: "Alarm_Cyclic_10ms"
    OsAlarmAction: TASK
    OsAlarmTaskRef: "Task_Cyclic_10ms"
    OsAlarmCyclic: TRUE
    OsAlarmAutoAdjust: TRUE
    OsAlarmCounterRef: "OsCounter"
    OsAlarmIncrement: 10   # 10ms
    OsAlarmMinCycle: 10

  # 100ms cyclic alarm
  - OsAlarmName: "Alarm_Cyclic_100ms"
    OsAlarmAction: TASK
    OsAlarmTaskRef: "Task_Cyclic_100ms"
    OsAlarmCyclic: TRUE
    OsAlarmAutoAdjust: TRUE
    OsAlarmCounterRef: "OsCounter"
    OsAlarmIncrement: 100  # 100ms
    OsAlarmMinCycle: 100
```

### OsEvent

```yaml
OsEvent:
  - OsEventName: "Event_DiagnosticRequest"
    OsEventMask: 0x01
    OsEventTaskRef: "Task_Event_Diag"
    OsEventAutoClear: TRUE
    OsEventKind: APPLICATION_EVENT
```

### OsResource

```yaml
OsResource:
  - OsResourceName: "RTE_OS_Resource"
    OsResourceProperty: STANDARD
    OsResourceCeilingPriority: 80

  - OsResourceName: "CanIf_OS_Resource"
    OsResourceProperty: STANDARD
    OsResourceCeilingPriority: 90

  - OsResourceName: "Com_OS_Resource"
    OsResourceProperty: STANDARD
    OsResourceCeilingPriority: 70
```

### OsApplication

```yaml
OsApplication:
  - OsApplicationName: "EngineControl_App"
    OsApplicationTrusted: FALSE
    OsApplicationSeparateAddressSpace: FALSE
    OsApplicationCoreId: 0
    OsApplicationChildProcess: FALSE
    OsApplicationAccessingApplication:
      - "Rte_EngineControl"
      - "CanIf"
      - "Com"
      - "Dem"
      - "NvM"
      - "WdgM"
```

---

## Memory Mapping

### Memory Sections

```
+-----------------------------------+---------+-----------+
| Section                           | Size    | Location  |
+-----------------------------------+---------+-----------+
| CODE (Executable code)            | 64 KB   | Flash     |
| RODATA (Constants, calibration)   | 8 KB    | Flash     |
| DATA (Initialized variables)      | 4 KB    | RAM       |
| BSS (Zero-initialized)            | 2 KB    | RAM       |
| STACK (Task stacks)               | 4 KB    | RAM       |
| NVM_EMULATION (NVM emulation)     | 64 KB   | Flash     |
+-----------------------------------+---------+-----------+
| Total Flash                       | 136 KB  |           |
| Total RAM                         | 10 KB   |           |
+-----------------------------------+---------+-----------+
```

### Linker Script Sections

```ld
MEMORY
{
  FLASH_CODE (rx)     : ORIGIN = 0x80000000, LENGTH = 64K
  FLASH_RODATA (r)    : ORIGIN = 0x80010000, LENGTH = 8K
  FLASH_NVM (rx)      : ORIGIN = 0x80012000, LENGTH = 64K
  RAM_DATA (rw)       : ORIGIN = 0x70000000, LENGTH = 6K
  RAM_BSS (rw)        : ORIGIN = 0x70001800, LENGTH = 2K
  RAM_STACK (rw)      : ORIGIN = 0x70002000, LENGTH = 4K
}

SECTIONS
{
  .code : {
    *(.text)
    *(.text.*)
  } > FLASH_CODE

  .rodata : {
    *(.rodata)
    *(.rodata.*)
  } > FLASH_RODATA

  .data : {
    _data_start = .;
    *(.data)
    *(.data.*)
    _data_end = .;
  } > RAM_DATA AT > FLASH_RODATA

  .bss : {
    _bss_start = .;
    *(.bss)
    *(.bss.*)
    *(COMMON)
    _bss_end = .;
  } > RAM_BSS

  .stack : {
    _stack_top = .;
    . = . + 4K;
    _stack_bottom = .;
  } > RAM_STACK
}
```

---

## Generated Files

```
results/bsw-config/
├── Can_Cfg.c                    # CAN module configuration
├── Can_Cfg.h                    # CAN module header
├── CanIf_Cfg.c                  # CAN Interface configuration
├── CanIf_Cfg.h                  # CAN Interface header
├── Com_Cfg.c                    # Communication module configuration
├── Com_Cfg.h                    # Communication module header
├── Dem_Cfg.c                    # Diagnostic Event Manager configuration
├── Dem_Cfg.h                    # Diagnostic Event Manager header
├── NvM_Cfg.c                    # NVM module configuration
├── NvM_Cfg.h                    # NVM module header
├── WdgM_Cfg.c                   # Watchdog Manager configuration
├── WdgM_Cfg.h                   # Watchdog Manager header
├── Os_Cfg.c                     # OS configuration (OSEK/VDX)
├── Os_Cfg.h                     # OS header
├── Os_Tasks.c                   # Task implementations
├── MemMap.h                     # Memory mapping definitions
├── Rte_BswM.c                   # BSW Mode Manager (if applicable)
└── BswM_Cfg.h                   # BSM Mode Manager header
```

---

## BSW Configuration Recommendations

### Priority 1 (Required)

- [x] All module configurations complete
- [x] All PDU signal mappings defined
- [x] All task/ alarm configurations defined
- [x] Memory sections defined and sized

**Status**: Ready for code generation

### Priority 2 (Recommended for Production)

- [ ] Configure E2E protection for safety-critical signals (ASIL-B)
- [ ] Add CanIf dynamic TX ID support if CAN ID remapping needed
- [ ] Configure Com signal gateway for cross-ECU signal routing
- [ ] Add Dem event aging parameters for all DTCs
- [ ] Configure NvM block callbacks for critical data

### Priority 3 (Optional Enhancements)

- [ ] Enable CanIf timestamping for diagnostic messages
- [ ] Add Com IPdu group handling for sleep/wake optimization
- [ ] Configure Dem OBD freeze frame expansion
- [ ] Add WdgM checkpoint paths for fine-grained supervision
- [ ] Configure Os application isolation for mixed-ASIL systems

---

## BSW Configuration Generation Command

```bash
# Generate BSW configuration using AUTOSAR BSW Configurator
autosar-bsw-config-generate \
  --input Can.arxml \
  --input CanIf.arxml \
  --input Com.arxml \
  --input Dem.arxml \
  --input NvM.arxml \
  --input WdgM.arxml \
  --input Os.arxml \
  --config BswConfig_EngineControl.yaml \
  --output results/bsw-config/ \
  --target tc397xp \
  --compiler gcc \
  --misra-check
```

---

## Next Steps

1. **Review BSW module configurations** for correctness
2. **Generate BSW code** using AUTOSAR BSW Generator
3. **Proceed to ECU extraction** using `autosar-ecu-extract` tool
4. **Integrate RTE + BSW + SWC** for full ECU build

---

## BSW Configuration Tool Metadata

- **Tool**: autosar-bsw-config
- **Version**: 1.2.0
- **AUTOSAR Release**: R22-11
- **Execution Duration**: 3.4 seconds
- **Input Files**: 7 ARXML configuration files
- **Exit Code**: 0 (Success)

---

## References

- AUTOSAR Classic Platform R22-11 - BSW Module Configuration Specification
- AUTOSAR Classic Platform R22-11 - OS Specification (OSEK/VDX compliant)
- AUTOSAR Classic Platform R22-11 - Communication Stack (Com, Can, CanIf)
- AUTOSAR Classic Platform R22-11 - Diagnostic Stack (Dem, Dcm)
- AUTOSAR Classic Platform R22-11 - NVM Specification
- AUTOSAR Classic Platform R22-11 - Watchdog Manager Specification
- ISO 26262-6:2018 - Product development at the software level
