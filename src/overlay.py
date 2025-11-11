"""Overlay window that displays attention warnings."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


class OverlayWindow(QtWidgets.QWidget):
    """Transparent overlay window that shows warning messages."""

    def __init__(self) -> None:
        super().__init__(None, QtCore.Qt.Tool | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self._message = ""
        self._size = QtCore.QSize(360, 140)
        self._position_percent = QtCore.QPointF(50.0, 12.0)

        self._label = QtWidgets.QLabel("", self)
        self._label.setAlignment(QtCore.Qt.AlignCenter)
        self._label.setWordWrap(True)
        self._label.setStyleSheet(
            """
            QLabel {
                color: #0f172a;
                background-color: rgba(254, 226, 226, 230);
                border-radius: 14px;
                padding: 20px 28px;
                font-size: 18px;
                font-weight: 600;
            }
            """
        )
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label, alignment=QtCore.Qt.AlignCenter)
        self.setMinimumSize(200, 100)
        self.hide()

    def configure(self, width: int, height: int, pos_x_percent: float, pos_y_percent: float) -> None:
        width = max(160, width)
        height = max(80, height)
        pos_x_percent = max(0.0, min(pos_x_percent, 100.0))
        pos_y_percent = max(0.0, min(pos_y_percent, 100.0))
        self._size = QtCore.QSize(width, height)
        self._position_percent = QtCore.QPointF(pos_x_percent, pos_y_percent)
        if self.isVisible():
            self._apply_geometry()

    def set_message(self, message: str) -> None:
        if message == self._message:
            return
        self._message = message
        if message:
            self._label.setText(message)
            self._apply_geometry()
            self.show()
            self.raise_()
        else:
            self._label.clear()
            self.hide()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:  # noqa: D401
        super().resizeEvent(event)
        if self._label:
            self._label.setFixedSize(self.size())

    def _apply_geometry(self) -> None:
        screen = QtGui.QGuiApplication.primaryScreen()
        if not screen:
            self.resize(self._size)
            return
        geometry = screen.availableGeometry()
        width = min(self._size.width(), geometry.width())
        height = min(self._size.height(), geometry.height())
        x_ratio = self._position_percent.x() / 100.0
        y_ratio = self._position_percent.y() / 100.0
        x_ratio = max(0.0, min(x_ratio, 1.0))
        y_ratio = max(0.0, min(y_ratio, 1.0))
        available_x = geometry.width() - width
        available_y = geometry.height() - height
        x = geometry.left() + int(available_x * x_ratio)
        y = geometry.top() + int(available_y * y_ratio)
        self.setGeometry(x, y, width, height)

