# qBarliman architecture

- **`qBarliman.py`:**

  - Application entry point.
  - Creates `QApplication` and `EditorWindowController`.

- **`controllers/editor_window_controller.py`:**

  - Creates and connects `View`, `ViewModel`, `TaskManager`, `SchemeDocument`.
  - Handles top-level UI events (like window showing).

- **`viewmodels/editor_window_viewmodel.py`:**

  - Holds observable UI state (using `Observable` properties).
  - Reacts to model changes and user input (via signals).
  - Commands `TaskManager` to run tasks.
  - Updates UI state based on task results.

- **`services/task_manager.py`:**

  - Manages the queue of Scheme tasks.
  - Interacts with `SchemeExecutionService` to run/kill processes.
  - Receives commands from `EditorWindowViewModel`.

- **`services/scheme_execution_service.py`:**

  - Executes Scheme code using `ProcessManager`.
  - Handles process output/errors.
  - Emits signals for task results.

- **`services/process_manager.py`:**
- Manages the external Scheme processes.
- Starts processes. Kills processesmachinations

- **`views/editor_window_ui.py`:**

  - Defines the UI layout (declarative).
  - Binds UI elements to `ViewModel` properties (via `update_ui`).
  - Emits signals for user input (text changes, etc.).

- **`models/scheme_document.py`:**

  - Wraps `SchemeDocumentData`.
  - Provides methods to update the document data (triggering signals).

- **`models/scheme_document_data.py`:**

  - Immutable data class holding the Scheme document's content.

- **`widgets/`:**

  - Custom Qt Widgets.

- **`utils/`:**

  - Utility functions and classes (logging, query building, etc.)

- **`templates.py`:** Holds scheme code templates
- **`constants.py`:** Holds project-wide constant variables and names

Here are the names of the relevant UI elements and ViewModel properties, broken down by category:

**UI Elements (in `EditorWindowUI`):**

- **Definition Text:**

  - `self.schemeDefinitionView` (a `SchemeEditorTextView`)

- **Best Guess:**

  - `self.bestGuessView` (a `SchemeEditorTextView`)

- **Test Inputs (1-6):**

  - `self.testInputs` (a _list_ of `SchemeEditorLineEdit` instances)
    - Individual inputs: `self.testInputs[0]`, `self.testInputs[1]`, ..., `self.testInputs[5]`

- **Test Expected Outputs (1-6):**

  - `self.testExpectedOutputs` (a _list_ of `SchemeEditorLineEdit` instances)
    - Individual outputs: `self.testExpectedOutputs[0]`, `self.testExpectedOutputs[1]`, ..., `self.testExpectedOutputs[5]`

- **Status Dialogs/Labels:**
  - **Definition Status:** `self.definitionStatusLabel` (a `QLabel`)
  - **Best Guess Status:** `self.bestGuessStatusLabel` (a `QLabel`)
  - **Test Statuses (1-6):** `self.testStatusLabels` (a _list_ of `QLabel` instances)
    - Individual statuses: `self.testStatusLabels[0]`, `self.testStatusLabels[1]`, ..., `self.testStatusLabels[5]`
  - **Error output**: `self.errorOutput`

**ViewModel Properties (in `EditorWindowViewModel`):**

- **Definition Text:**

  - `self.definition_text` (an `Observable` property)

- **Best Guess:**

  - `self.best_guess` (an `Observable` property)

- **Test Inputs:**

  - `self.test_inputs` (an `Observable` property of type `list`)

- **Test Expected Outputs:**

  - `self.test_expected` (an `Observable` property of type `list`)

- **Status:**
  _ **Definition Status:** `self.definition_status` (an `Observable` property, a tuple: `(text, TaskStatus)`)
  _ **Best Guess Status:** `self.best_guess_status` (an `Observable` property, a tuple: `(time_string, TaskStatus)`)

  - **Test Statuses:** `self.test_statuses` (an `Observable` property, a _list_ of tuples: `[(index, time_string, TaskStatus), ...]`)
  - **Error Output:** `self.error_output` (Observable property of str)
    **Key Points:**

- The UI elements are accessed directly on the `self.view` instance within the `EditorWindowController`.
- The ViewModel properties are accessed on the `self.view_model` instance within the `EditorWindowController`.
- Lists are used for the test inputs, expected outputs, and status labels, reflecting the multiple test cases. You access individual elements using indexing (e.g., `self.view.testInputs[0]` for the first test input).
- The viewmodel properties use the `Observable` class.

This provides a complete mapping between the UI elements you interact with and the underlying data representation in the ViewModel. This clear separation is fundamental to the Model-View-ViewModel (MVVM) and reactive programming approach.
