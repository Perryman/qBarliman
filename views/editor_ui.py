from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QSplitter, QVBoxLayout, QWidget

from .editor_style import apply_style_to_component


class EditorUI(QWidget):
    """Editor UI that dynamically builds itself using a declarative component registry."""

    def __init__(self, main_window, component_registry, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.main_window.setWindowTitle("qBarliman")
        self.component_registry = component_registry
        self._setup_font()
        self._build_ui()
        self._apply_styles()

    def _setup_font(self):
        self.default_font = QFont()
        self.default_font.setStyleHint(QFont.Monospace)
        self.default_font.setFamily("Source Code Pro")
        self.default_font.setPointSize(16)
        self.default_font.setFixedPitch(True)
        self.default_font.setFamilies(
            ["Source Code Pro", "SF Mono", "Lucida Console", "Monaco", "Courier New"]
        )

    def _build_ui(self):
        """Dynamically builds the UI based on the component registry."""
        self.setMinimumWidth(1000)
        self.setMinimumHeight(800)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Vertical, self)

        # Map section types to builder functions.
        builders = {
            "vertical": self._build_vertical_section,
            "grid": self._build_grid_section,
        }

        section_widgets = []
        grid_widget = None

        # Iterate over each section in the registry.
        for section in self.component_registry.values():
            section_type = section.get("type", "vertical")
            if builder := builders.get(section_type):
                widget = builder(section.get("components", {}), section)
                splitter.addWidget(widget)
                section_widgets.append(widget)
                if section_type == "grid":
                    grid_widget = widget

        self._set_splitter_sizes(splitter, section_widgets, grid_widget)
        main_layout.addWidget(splitter)

    def _set_splitter_sizes(self, splitter, section_widgets, grid_widget):
        """Helper to calculate and set proportional sizes for the splitter sections."""
        grid_height = grid_widget.sizeHint().height() if grid_widget else 100
        num_other = len(section_widgets) - (1 if grid_widget else 0)
        remaining = self.height() - grid_height
        other_height = int(remaining / num_other) if num_other > 0 else 0
        sizes = [
            grid_height if widget is grid_widget else other_height
            for widget in section_widgets
        ]
        if sizes:
            splitter.setSizes(sizes)

    def _build_vertical_section(self, components, section):
        """Builds a vertical section with rows based on their declared type."""
        section_widget = QWidget(self)
        layout = QVBoxLayout(section_widget)
        layout.setContentsMargins(2, 2, 2, 2)

        if rows := section.get("rows"):
            for row in rows:
                row_type = row.get("type", "horizontal")
                order = row.get("order", [])
                if row_type == "horizontal":
                    self._add_horizontal_row(layout, components, order)
                elif row_type == "single":
                    self._add_single_row(layout, components, order)
        else:
            self._add_components(layout, components)
        return section_widget

    def _add_horizontal_row(self, layout, components, order):
        """Adds a horizontal row of components."""
        row_widget = QWidget(self)
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(2, 2, 2, 2)
        for key in order:
            if comp_def := components.get(key):
                widget = (
                    comp_def.get("widget", comp_def)
                    if isinstance(comp_def, dict)
                    else comp_def
                )
                row_layout.addWidget(widget, 0)
        layout.addWidget(row_widget)

    def _add_single_row(self, layout, components, order):
        """Adds a single row of components."""
        for key in order:
            if comp_def := components.get(key):
                widget = (
                    comp_def.get("widget", comp_def)
                    if isinstance(comp_def, dict)
                    else comp_def
                )
                layout.addWidget(widget)

    def _add_components(self, layout, components):
        """Fallback: adds all components directly to the layout."""
        for comp_def in components.values():
            widget = (
                comp_def.get("widget", comp_def)
                if isinstance(comp_def, dict)
                else comp_def
            )
            layout.addWidget(widget)

    def _build_grid_section(self, components, section=None):
        """Builds a grid section (e.g., for tests) with configurable alignments."""
        grid_widget = QWidget(self)
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(2, 2, 2, 2)
        grid_layout.setSpacing(2)

        rows = components.get("rows", {})
        for row_index, row_components in rows.items():
            for col_index, (_comp_name, comp_def) in enumerate(row_components.items()):
                if isinstance(comp_def, dict):
                    widget = comp_def.get("widget")
                    role = comp_def.get("role")
                else:
                    widget = comp_def
                    role = None
                grid_layout.addWidget(widget, row_index, col_index)
                if role:
                    apply_style_to_component(widget, role)
                    if role == "status_indicator":
                        grid_layout.setAlignment(
                            widget, Qt.AlignRight | Qt.AlignVCenter
                        )
        return grid_widget

    def _apply_styles(self):
        """Recursively apply styles to all components in the registry."""

        def apply_styles_in_dict(comp_dict):
            for _key, value in comp_dict.items():
                if isinstance(value, dict):
                    if "widget" in value and "role" in value:
                        apply_style_to_component(value["widget"], value["role"])
                    else:
                        apply_styles_in_dict(value)

        for section in self.component_registry.values():
            if "components" in section:
                apply_styles_in_dict(section["components"])
