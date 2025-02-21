| Component/Module              | Responsibility                                                                                                                                                                          | Interactions/Observations                                                                                                                                                                    |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| qBarliman.py                  | - Application entry point<br>- Sets up the overall application environment                                                                                                              | - Instantiates editor_window_controller.py to bootstrap the application                                                                                                                      |
| editor_window_controller.py   | - Initializes necessary observer classes<br>- Connects these classes using PySide6’s @signal and @slot decorators at startup                                                            | - Simply wires up components for decoupled communication                                                                                                                                     |
| editor_window_ui.py           | - Builds and manages the UI layout (text boxes, status labels, dynamic test sections, error box, etc.)<br>- Loads defaults from ./config/constants.py                                   | - Emits user interaction signals and updates display based on signals received                                                                                                               |
| editor_window_task_manager.py | - Listens for UI changes<br>- Cancels running tasks and debounces input via a QTimer<br>- Initiates tasks based on current UI state<br>- Delegates specialized tasks                    | - Receives complete task state updates (e.g., task objects containing task_id, task_name, task_result, etc.)<br>- Delegates Scheme queries to the query builder and scheme execution service |
| process_manager.py            | - Manages the creation, monitoring, and termination of external/internal processes                                                                                                      | - Invoked by the task manager or by the scheme execution service when heavy tasks require isolated processing                                                                                |
| scheme_execution_service.py   | - Specializes in interpreting and executing Scheme (.scm) queries<br>- Handles pre-processing (parsing/validation) and post-processing<br>- May delegate heavy tasks to process manager | - Receives Scheme-specific tasks from the task manager (often indirectly via the query builder)                                                                                              |
| scheme_document.py            | - Encapsulates the Scheme document model<br>- Holds field validation logic and status tracking<br>- Maintains the business logic state (logic array/state dict)                         | - Provides the business logic for Scheme validation to the UI and may influence query building                                                                                               |
| query_builder.py              | - Constructs queries based on the current UI inputs and scheme document state<br>- Utilizes its internal logic to validate and formulate proper queries                                 | - Listens for signals related to user input/model changes<br>- Emits a signal with the new query to the task manager once the query is ready                                                 |

### How the Query Builder Integrates

**Signal Reception:**
The query builder listens to key signals from the UI or from the scheme document model that indicate when input has changed or when a new query should be derived.

**Query Construction:**
Upon receiving these signals, the query builder builds (or updates) its internal query representation—ensuring that it adheres to the necessary syntax and logic.

**Emission of the Final Query:**
Once validated, the query builder emits a new query signal. The task manager, which is subscribed to this signal, then takes the query and delegates its execution (perhaps via the scheme execution service and, if needed, the process manager).

### Conclusion

Implementing a query builder adds clarity and separation:

- **Decoupling:** The UI doesn't have to handle query logic directly, and the task manager is freed from lower-level details.
- **Flexibility:** If your query logic becomes more complex, it’s neatly encapsulated in its dedicated module.
- **Scalability:** Future modifications related to query logic remain localized to query_builder.py.
