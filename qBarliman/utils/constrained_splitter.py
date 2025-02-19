from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter


class ConstrainedSplitter(QSplitter):
    def __init__(
        self,
        orientation=Qt.Orientation.Horizontal,
        parent=None,
        min_sizes=None,
        max_sizes=None,
    ):
        super().__init__(orientation, parent)
        self.min_sizes = min_sizes or []
        self.max_sizes = max_sizes or []

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Enforce minimum sizes if provided.
        if self.min_sizes:
            sizes = self.sizes()
            for i, min_size in enumerate(self.min_sizes):
                sizes[i] = max(sizes[i], min_size)
            self.setSizes(sizes)
        # Enforce maximum sizes if provided.
        if self.max_sizes:
            sizes = self.sizes()
            for i, max_size in enumerate(self.max_sizes):
                sizes[i] = min(sizes[i], max_size)
            self.setSizes(sizes)
