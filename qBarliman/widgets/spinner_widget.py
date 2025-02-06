from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt, QTimer, QSize, QRectF

class SpinnerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.is_spinning = False
        self.setFixedSize(16, 16)  # Match NSProgressIndicator size
        
    def startAnimation(self):
        self.show()
        self.is_spinning = True
        self.timer.start(50)  # 20 fps
        
    def stopAnimation(self):
        self.is_spinning = False
        self.timer.stop()
        self.hide()
        
    def rotate(self):
        self.angle = (self.angle + 30) % 360
        self.update()
        
    def paintEvent(self, event):
        if not self.is_spinning:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = min(self.width(), self.height()) - 2
        rect = QRectF((self.width() - width) / 2, 
                     (self.height() - width) / 2,
                     width, width)
        
        painter.translate(rect.center())
        painter.rotate(self.angle)
        painter.translate(-rect.center())
        
        gradient_stops = [
            (0.0, QColor(0, 0, 0, 255)),
            (0.5, QColor(0, 0, 0, 127)),
            (1.0, QColor(0, 0, 0, 0))
        ]
        
        for i in range(8):
            color = QColor(0, 0, 0, int(255 * (1 - i/8)))
            painter.fillRect(rect, color)
            painter.rotate(45)

    def sizeHint(self):
        return QSize(16, 16)
