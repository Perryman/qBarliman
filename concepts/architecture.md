# qBarliman architecture

## Reactive Signal-Driven Architecture (RSDA)

qBarliman implements a Reactive Signal-Driven Architecture that combines several modern patterns:

- **Reactive State Propagation**: Changes to state trigger UI updates through signals
- **Unidirectional Data Flow**: Data flows predictably from UI → Model → Processing → Model → UI
- **Declarative Component Configuration**: UI elements defined through data structures
- **Dynamic Signal Wiring**: Signals and slots connected programmatically
- **Functional Slot Factories**: Reusable functions that create specialized slot handlers
- **Component Registry Pattern**: UI elements stored in dictionaries for programmatic access
- **Centralized State Management**: Single source of truth drives all UI updates
- **Signal-Based Initialization**: Default values flow through the same paths as runtime updates

## Component Structure

- **`qBarliman.py`:**

  - Application entry point.
  - Creates `QApplication` and `EditorWindowController`.

- **`controllers/editor_window_controller.py`:**

  - Creates and wires components using dynamic signal connections
  - Establishes unidirectional data flow between components
  - Configures signal-slot pathways for state propagation

- **`viewmodels/editor_window_viewmodel.py`:**

  - Implements centralized state management with observable properties
  - Maintains the single source of truth for UI state
  - Emits signals when state changes occur
  - Processes incoming state change requests from UI

- **`services/task_manager.py`:**

  - Responds to state change signals from ViewModel
  - Manages task lifecycle through the signal system
  - Uses functional slot factories for specialized task handling

- **`services/scheme_execution_service.py`:**

  - Executes Scheme code using `ProcessManager`.
  - Emits signals with execution results feeding back into the state system
  - Maintains stateless execution pattern - all state exists in ViewModel

- **`services/process_manager.py`:**

  - Manages external Scheme processes
  - Converts process events into signals for the reactive system

- **`views/editor_window_ui.py`:**

  - Implements declarative component configuration
  - Uses component registry pattern for programmatic UI access
  - Connects UI elements to signal pathways via dynamic signal wiring
  - UI elements reflect state without maintaining state themselves

- **`models/scheme_document.py`:**

  - Emits state change signals that integrate with the reactive system
  - Provides state update methods that maintain unidirectional data flow

- **`models/scheme_document_data.py`:**

  - Immutable data structures that represent system state
  - Designed for efficient state comparison and change detection

- **`widgets/`:**

  - Custom Qt Widgets designed for the reactive architecture
  - Components emit signals but don't maintain application state

- **`utils/`:**

  - Signal utility functions and factories
  - State transformation helpers

- **`templates.py`:** Holds scheme code templates
- **`constants.py`:** Holds project-wide constant variables and names

## UI and ViewModel Mapping

**UI Component Registry (in `EditorWindowUI`):**

- **Definition Text:**

  - `self.components["definition"]["view"]` (a `SchemeEditorTextView`)

- **Best Guess:**

  - `self.components["best_guess"]["view"]` (a `SchemeEditorTextView`)

- **Test Inputs:**

  - `self.components["tests"][test_index]["input"]["view"]` (a `SchemeEditorLineEdit`)

- **Test Expected Outputs:**

  - `self.components["tests"][test_index]["expected"]["view"]` (a `SchemeEditorLineEdit`)

- **Status Elements:**
  - `self.components["definition"]["status"]` (a `QLabel`)
  - `self.components["best_guess"]["status"]` (a `QLabel`)
  - `self.components["tests"][test_index]["status"]` (a `QLabel`)
  - `self.components["error_output"]` (a `QTextEdit`)

**ViewModel State (in `EditorWindowViewModel`):**

- **Central State Object:**

  - `self.state` (an observable state container)

- **State Properties:**
  - `self.state.definition.text` (observable string)
  - `self.state.best_guess.text` (observable string)
  - `self.state.tests[index].input` (observable string)
  - `self.state.tests[index].expected` (observable string)
  - `self.state.definition.status` (observable status object)
  - `self.state.best_guess.status` (observable status object)
  - `self.state.tests[index].status` (observable status object)
  - `self.state.error_output` (observable string)

## Signal Flow

1. **UI Events** → emit signals with new input values
2. **ViewModel** → receives signals, updates central state, emits state change signals
3. **TaskManager** → receives state change signals, executes tasks based on new state
4. **SchemeExecutionService** → processes tasks, emits result signals
5. **ViewModel** → receives result signals, updates state, emits state change signals
6. **UI Components** → receive state change signals, update their visual representation

This architecture provides a predictable, unidirectional data flow while leveraging Qt's signal-slot mechanism. It eliminates direct dependencies between components, allowing for easier testing and maintenance.
