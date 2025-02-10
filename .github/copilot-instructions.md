# qBarliman Project Guidelines

## Core Principles

- **Vision**: Create a cross-platform Python 3, Qt 6 GUI program.
- **GUI Development**: Use PySide6 for Qt 6 development. Avoid PyQt6.
- **Scheme Handling**: Use string templates for Scheme code generation. Keep reference implementations intact.
- **External Execution**: Launch Scheme programs externally and ensure proper UI interop.
- **Project Size**: Keep the project small, simple, and minimal. UI should be basic but functional.
- **Dependencies**: Use a minimal number of libraries. Avoid unnecessary dependencies.

## Development Practices

- **MVC Pattern**: Implement strict separation of concerns:
  - **Model**: Encapsulate business logic and data storage.
  - **View**: Handle UI presentation and user interaction.
  - **Controller**: Coordinate between model and view.
- **Communication**: Use signals and slots for decoupled communication between model and view.
- **Property Decorators**: Use `Property` decorators in models to expose properties and notify changes.
- **Loose Coupling**: Ensure components are loosely coupled for easy testing and maintenance.

## Logging and Debugging

- **Logging System**: Use provided logging system with enum: WARN, GOOD, INFO, DEBUG.
- **Console Logs**: Keep logs meaningful and avoid unnecessary verbosity.

## Performance and Threading

- **Timers**: Implement timers for asynchronous operations. Avoid spinners.
- **Threading**: Use QThreadPool for background tasks. Avoid GUI updates from non-main threads.

## Code Quality and Maintenance
- **Clean Code**: Maintain a clean, modular, and well-documented codebase.
- **Comments**: Remove any unnecessary comments or TODOs.
- **Testing**: Test all components separately. Use unit tests for core logic.
