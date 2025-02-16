# PySide6 Application Pattern Guide

## Core Pattern: Observable View Model with Dependency Injection

We use a metaclass-based observable pattern with dependency injection for PySide6 apps. Also, when encountering a series of if statements with various items, refactor them to use a common interface. This ensures that all items have the same input, and the concrete implementations handle the specific behaviors (strategy pattern).

```python
# Core pattern example
class Observable(Generic[T]):
    """Descriptor for auto-signal properties"""
    def __init__(self, type_: Type[T], default: T = None):
        self.type_ = type_
        self.default = default

    def __set_name__(self, owner, name):
        self.name = name
        setattr(owner, f"{name}_changed", Signal(self.type_))

class ViewModel(QObject, metaclass=ViewModelMeta):
    """Base class for view models with observable properties"""
    title = Observable(str, "")
    count = Observable(int, 0)
    items = Observable(List[str], [])

class View(QWidget):
    """View binds to ViewModel properties"""
    def __init__(self, view_model: ViewModel):
        self.view_model = view_model
        self.bind_view_model()

    def bind_view_model(self):
        self.view_model.title_changed.connect(self.title_label.setText)
```

## Project Structure

```sh
app/
  models/      # Immutable dataclasses
  viewmodels/  # Observable state + logic
  views/       # UI components
  services/    # Business logic
```

## Key Principles

1. **Observable Properties**: Use `Observable` descriptors for auto-signals
2. **View Models**: Hold state and logic, emit change signals
3. **Dependency Injection**: Views receive view models
4. **Immutable Models**: Use dataclasses for data
5. **Declarative Bindings**: Connect signals to slots directly

## Anti-Patterns to Avoid

❌ Direct UI updates from services
❌ Complex event handlers
❌ UI files or Qt Designer
❌ Manual signal/slot management

## Quick Examples

### Good
```python
# View Model with observable properties
class EditorViewModel(ViewModel):
    code = Observable(str)
    result = Observable(str)
    error = Observable(str)

# View binds to view model
class EditorView(QWidget):
    def __init__(self, vm: EditorViewModel):
        self.vm = vm
        self.vm.code_changed.connect(self.editor.setText)
        self.vm.error_changed.connect(self.show_error)
```

### Bad
```python
# ❌ Don't do this
class Editor:
    def update_ui(self):
        self.label.setText(self.get_status())
    
    def on_button_click(self):
        self.update_ui()
```

This pattern:
1. Reduces boilerplate through metaclasses
2. Automates signal/slot connections
3. Makes state changes predictable
4. Simplifies testing
5. Enforces clean architecture

The key is using observable properties in view models that automatically emit signals, then binding views to those signals. This replaces manual event handling with declarative data flow.
