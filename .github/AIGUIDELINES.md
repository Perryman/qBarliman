# PySide6 GUI Development Guidelines (Python-Centric, Declarative)

These guidelines focus on building maintainable PySide6 applications using a purely Python-based, declarative style, emphasizing separation of concerns and immutability. **We are _not_ using Qt Designer or `.ui` files.**

**1. Project Structure:**

- **Modules:**
  - `qBarliman.py`: Entry point (minimal).
  - `views/`: UI layout and structure (one file per major component).
  - `widgets/`: Reusable, custom widgets.
  - `controllers/`: Connects UI and model (view model).
  - `models/`: Immutable data classes and `QObject` wrappers.
  - `operations/`: Asynchronous operations (no UI logic).
  - `utils/`: Reusable helper functions.
  - `resources/`: Icons, images, etc. (if needed).
- **File Size:** Keep files under 200 lines.

**2. UI (`views/` and `widgets/`):**

- **Declarative Layout:** Define UI layout _directly in Python_ using layout managers (`QVBoxLayout`, `QHBoxLayout`, `QGridLayout`). No `.ui` files.

  ```python
  # Example: views/my_view.py
  from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

  class MyView(QWidget):
      def __init__(self):
          super().__init__()
          layout = QVBoxLayout(self)
          self.label = QLabel("Initial Text")
          self.button = QPushButton("Click Me")
          layout.addWidget(self.label)
          layout.addWidget(self.button)
  ```

- **Custom Widgets (`widgets/`):** Subclass Qt widgets for reusable components.
- **Views orchestrate Widgets**

**3. Signals, Slots, and Events:**

- **`@Slot` and `Signal`:** Use Qt's signals and slots for _all_ communication. No direct method calls between components.
- **`@Slot`:** Decorate methods connected to signals. Use argument types.
  ```python
  @Slot(str)
  def update_label(self, text):
      self.label.setText(text)
  ```
- **`Signal`:** Define custom signals in classes inheriting from `QObject`. Specify argument types.
- **Lambdas in `connect()`:** Use lambdas directly for concise, asynchronous handling, especially with `QProcess`. Avoid many small `handle_...` methods.
  ```python
  # Example (operations/process_manager.py)
  self.process.readyReadStandardOutput.connect(
      lambda: self.processOutput.emit(self.process.readAllStandardOutput().data().decode(), "")
  )
  ```
- **Event Handlers (Optional):** For complex model updates, consider a decorator-based event handler (like `event_handler`), but prioritize signals/slots for most interactions.

**4. Model:**

- **Immutable Data:** Use `dataclasses.dataclass(frozen=True)` or similar for immutable model data.
- **`QObject` Wrapper:** Wrap the data class in a `QObject` for Qt signal/slot integration. Emit signals on data changes.

**5. Asynchronous Operations (`operations/`):**

- **No UI Logic:** `operations/` classes manage asynchronous tasks (e.g., `QProcess` via a `ProcessManager`). They _only_ communicate via signals.
- **NO `ui_update_interface.py`:** Operations do _not_ update the UI. UI listens to signals.

**6. General:**

- **Separation of Concerns:** Strictly separate UI, logic, and data.
- **DRY:** Don't repeat yourself.
- **KISS:** Keep it simple.
- **Immutability:** Favor immutable data structures.
- **Inversion of Control:** Components _provide_ data/events, they don't _control_ how they're used.

**Simplified Signal/Slot/Abstraction Guide:**

| Feature                | When to Use                                                 | Notes                                            |
| ---------------------- | ----------------------------------------------------------- | ------------------------------------------------ |
| `@Slot`                | Methods connected to signals.                               | Use argument types.                              |
| `Signal`               | Defining custom signals (class must inherit `QObject`).     | Specify argument types.                          |
| Lambdas in `connect()` | Concise asynchronous handling (especially with `QProcess`). | Avoid many small `handle_...` methods.           |
| Immutable Data Classes | Representing the application's state.                       | `dataclasses.dataclass(frozen=True)` or similar. |
| `QObject` Wrapper      | Integrate immutable data with Qt's signals/slots.           | Wrapper emits signals on data changes.           |
