from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy

# Central style registry defining appearance for all UI roles.
STYLE_REGISTRY = {
    "roles": {
        "section_label": {
            "size_policy": (QSizePolicy.Minimum, QSizePolicy.Preferred),
            "alignment": None,
        },
        "status_indicator": {
            "size_policy": (QSizePolicy.Fixed, QSizePolicy.Preferred),
            "alignment": Qt.AlignRight | Qt.AlignVCenter,
        },
        "editor": {
            "size_policy": (QSizePolicy.Expanding, QSizePolicy.Expanding),
        },
        "test_input": {
            "size_policy": (QSizePolicy.Expanding, QSizePolicy.Minimum),
        },
        "test_expected": {
            "size_policy": (QSizePolicy.Expanding, QSizePolicy.Minimum),
        },
    }
}

# Mapping of style keys to functions that apply that style property.
STYLE_APPLIERS = {
    "alignment": lambda widget, value: (
        widget.setAlignment(value) if value is not None else None
    ),
    "size_policy": lambda widget, value: widget.setSizePolicy(*value),
}


def apply_style_to_component(widget, role):
    """Apply style settings from the style registry to a widget based on its role."""
    style = STYLE_REGISTRY["roles"].get(role, {})
    for key, value in style.items():
        if key in STYLE_APPLIERS:
            STYLE_APPLIERS[key](widget, value)
        elif hasattr(widget, key):
            setattr(widget, key, value)
