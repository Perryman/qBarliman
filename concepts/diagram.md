# Class Diagram for qBarliman Application

classDiagram
direction LR

    class qBarliman {
        +main()
    }

    class EditorWindowController {
        +initializeObservers()
        +connectSignalsSlots()
    }

    class EditorWindowUI {
        +buildUILayout()
        +loadDefaults()
        +emitUserInteractionSignals()
        +updateDisplay()
    }

    class EditorWindowTaskManager {
        +listenForUIChanges()
        +cancelRunningTasks()
        +debounceInput()
        +initiateTasks()
        +delegateTasks()
        +emitTaskStateUpdates()
    }

    class ProcessManager {
        +createProcess()
        +monitorProcess()
        +terminateProcess()
        +emitProcessOutput()
    }

    class SchemeExecutionService {
        +interpretSchemeQueries()
        +handlePreProcessing()
        +handlePostProcessing()
        +delegateHeavyTasks()
        +emitTaskResultReady()
        +handleProcessOutput()
    }

    class SchemeDocument {
        +encapsulateModel()
        +validateFields()
        +trackStatus()
        +maintainBusinessLogic()
        +emitModelChanges()
    }

    class QueryBuilder {
        +constructQueries()
        +validateQueries()
        +emitQuerySignal()
    }

    %% Relationships & Wiring:
    qBarliman --> EditorWindowController : "bootstrap/init"
    EditorWindowController --> EditorWindowUI : "initialize UI"
    EditorWindowController --> EditorWindowTaskManager : "initialize Task Manager"
    EditorWindowUI --> EditorWindowTaskManager : "userInteractionSignals"
    EditorWindowTaskManager --> ProcessManager : "* delegate heavy tasks"
    EditorWindowTaskManager --> SchemeExecutionService : "scheme query tasks"
    SchemeExecutionService --> ProcessManager : "* delegate heavy processing"
    EditorWindowTaskManager --> QueryBuilder : "pass updates for query building"
    QueryBuilder --> SchemeDocument : "build queries from model"
    SchemeDocument --> EditorWindowUI : "inform UI of model state"

    %% Signal/Slot Flow Annotations:
    EditorWindowUI ..> EditorWindowTaskManager : "emitUserInteractionSignals()"
    EditorWindowTaskManager ..> EditorWindowUI : "emitTaskStateUpdates()"
    SchemeExecutionService ..> EditorWindowTaskManager : "emitTaskResultReady()"
    ProcessManager ..> SchemeExecutionService : "emitProcessOutput()"
    QueryBuilder ..> EditorWindowTaskManager : "emitQuerySignal()"
    SchemeDocument ..> QueryBuilder : "emitModelChanges()"

    %% Example of annotation:
    <<service>> SchemeExecutionService
