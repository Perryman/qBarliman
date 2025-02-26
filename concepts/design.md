# qBarliman Design - Reactive Signal-Driven Architecture

| Component/Module            | Responsibility                                                                                                                                                                            | Interactions/Observations                                                                                                                                              |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| qBarliman.py                | - Application entry point - Sets up the overall application environment - Initializes the reactive signal framework                                                                       | - Instantiates the controller which initializes the reactive signal architecture                                                                                       |
| editor_window_controller.py | - Establishes the component registry - Configures dynamic signal connections - Sets up unidirectional data flow pathways - Initializes centralized state management                       | - Creates functional slot factories for component interaction - Orchestrates the signal flow between components without tight coupling                                 |
| editor_window_ui.py         | - Implements declarative component configuration - Creates the component registry for UI elements - Connects UI elements to the signal system - Loads defaults from ./config/constants.py | - Emits user interaction signals via standard pattern - Updates UI based on received state change signals - Does not maintain application state                        |
| editor_window_viewmodel.py  | - Implements centralized state container - Manages observable properties - Processes state change requests - Maintains the single source of truth                                         | - Emits state change signals when properties are updated - Transforms UI signals into state updates - Drives the entire application through reactive state propagation |
| task_manager.py             | - Reactively processes state changes - Uses functional slot factories for task handling - Manages task lifecycles - Signals task state transitions                                        | - Subscribes to state change signals - Emits task state signals - Delegates specialized tasks through the signal system                                                |
| process_manager.py          | - Manages external process lifecycle events - Converts process I/O into signals - Maintains process isolation                                                                             | - Communicates process state through signals - Responds to task lifecycle signals                                                                                      |
| scheme_execution_service.py | - Reactively executes Scheme code based on state changes - Transforms execution results into signals - Maintains stateless execution pattern                                              | - Subscribes to task signals - Emits execution result signals - Integrates with process manager through signal interface                                               |
| scheme_document.py          | - Encapsulates the Scheme document model - Emits model change signals - Provides state update methods                                                                                     | - Integrates with the reactive signal system - Updates based on signals from the viewmodel - Emits signals when document state changes                                 |
| query_builder.py            | - Reactively builds queries based on state changes - Implements signal-based validation - Emits query-ready signals                                                                       | - Subscribes to state change signals - Emits query-ready signals when valid queries are constructed - Participates in the unidirectional data flow                     |

## Reactive Signal Flow

The Reactive Signal-Driven Architecture in qBarliman follows these key principles:

### 1. Unidirectional Data Flow

Data flows in one direction through the application:

```txt
UI Events → ViewModel → Task Manager → Execution Services → ViewModel → UI Update
```

This predictable flow makes the application behavior easier to understand, test, and debug.

### 2. Component Registry Pattern

UI elements are organized in a registry for programmatic access:

```python
self.components = {
    "definition": {
        "view": SchemeEditorTextView(),
        "status": QLabel()
    },
    "best_guess": {
        "view": SchemeEditorTextView(),
        "status": QLabel()
    },
    "tests": [
        {
            "input": { "view": SchemeEditorLineEdit() },
            "expected": { "view": SchemeEditorLineEdit() },
            "status": QLabel()
        },
        # Additional tests...
    ]
}
```

This structure enables dynamic signal wiring and consistent access patterns.

### 3. Dynamic Signal Wiring

Signals and slots are connected programmatically, creating a flexible communication network:

```python
# Example dynamic signal connection
for test_index in range(6):
    input_component = self.components["tests"][test_index]["input"]["view"]
    input_component.textChanged.connect(
        create_test_input_handler(self.view_model, test_index)
    )
```

### 4. Functional Slot Factories

Specialized slot handlers are created with factory functions:

```python
def create_test_input_handler(view_model, test_index):
    def handle_test_input_change(text):
        view_model.update_test_input(test_index, text)
    return handle_test_input_change
```

This approach reduces boilerplate while maintaining the reactive pattern.

### 5. Centralized State Management

The ViewModel maintains all application state in a single observable container:

```python
self.state = ObservableState({
    "definition": { "text": "", "status": None },
    "best_guess": { "text": "", "status": None },
    "tests": [
        {"input": "", "expected": "", "status": None},
        # Additional tests...
    ],
    "error_output": ""
})
```

This centralization ensures consistency and enables predictable state transitions.

## Benefits of the RSDA Pattern in qBarliman

- **Decoupling:** Components communicate through signals without direct dependencies.
- **Testability:** Each component can be tested in isolation by simulating signals.
- **Consistency:** State changes follow a single predictable path.
- **Flexibility:** New components can be added without modifying existing ones.
- **Maintainability:** Localized changes have minimal impact on the system as a whole.
