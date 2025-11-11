"""Application entry point for the gaze and head tracker GUI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

try:
    from .calibration import CalibrationManager
    from .gaze_head_tracker import GazeHeadTracker
    from .overlay import OverlayWindow
except ImportError:
    from calibration import CalibrationManager
    from gaze_head_tracker import GazeHeadTracker
    from overlay import OverlayWindow


class VideoWidget(QtWidgets.QLabel):
    """Widget that displays video frames with overlays."""

    def __init__(self) -> None:
        super().__init__()
        self.setScaledContents(False)
        self.setFixedSize(640, 480)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.setStyleSheet("background-color: #f0f4f8; border: 1px solid #cbd5e1;")

    def set_frame(
        self,
        frame: np.ndarray,
        landmarks: Optional[list[tuple[int, int]]] = None,
        head_angles: Optional[Tuple[float, float, float]] = None,
        gaze_vector: Optional[Tuple[float, float]] = None,
        iris_positions: Optional[Tuple[Tuple[float, float], Tuple[float, float]]] = None,
    ) -> None:
        frame_to_draw = frame.copy()
        if landmarks:
            for x, y in landmarks:
                cv2.circle(frame_to_draw, (x, y), 1, (0, 200, 120), -1)
        
        if iris_positions:
            left_iris, right_iris = iris_positions
            cv2.circle(frame_to_draw, (int(left_iris[0]), int(left_iris[1])), 3, (0, 120, 255), -1)
            cv2.circle(frame_to_draw, (int(right_iris[0]), int(right_iris[1])), 3, (0, 120, 255), -1)
            cv2.circle(frame_to_draw, (int(left_iris[0]), int(left_iris[1])), 5, (255, 200, 0), 2)
            cv2.circle(frame_to_draw, (int(right_iris[0]), int(right_iris[1])), 5, (255, 200, 0), 2)
        
        overlay_lines = []
        if head_angles:
            yaw, pitch, roll = head_angles
            overlay_lines.append(f"Yaw (left/right): {yaw:+.1f} deg")
            overlay_lines.append(f"Pitch (up/down): {pitch:+.1f} deg")
            overlay_lines.append(f"Roll (tilt): {roll:+.1f} deg")
        if gaze_vector:
            horizontal, vertical = gaze_vector
            overlay_lines.append(f"Gaze horizontal: {horizontal:+.2f}")
            overlay_lines.append(f"Gaze vertical: {vertical:+.2f}")
        
        for index, line in enumerate(overlay_lines):
            position = (12, 24 + index * 22)
            cv2.putText(
                frame_to_draw,
                line,
                position,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (15, 23, 42),
                3,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame_to_draw,
                line,
                position,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
        
        rgb_frame = cv2.cvtColor(frame_to_draw, cv2.COLOR_BGR2RGB)
        height, width, channel = rgb_frame.shape
        bytes_per_line = channel * width
        qt_image = QtGui.QImage(rgb_frame.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
        self.setPixmap(QtGui.QPixmap.fromImage(qt_image))


class OverlayPreview(QtWidgets.QWidget):
    """Tiny preview widget to visualise overlay placement."""

    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(220, 140)
        self._screen_size = QtCore.QSize(1920, 1080)
        self._overlay_config = (320, 140, 50.0, 12.0)

    def update_preview(
        self,
        screen_size: QtCore.QSize,
        overlay_width: int,
        overlay_height: int,
        pos_x_percent: float,
        pos_y_percent: float,
    ) -> None:
        if screen_size.width() > 0 and screen_size.height() > 0:
            self._screen_size = screen_size
        self._overlay_config = (overlay_width, overlay_height, pos_x_percent, pos_y_percent)
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:  # noqa: D401
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor("#f1f5f9"))

        margin = 12
        screen_rect = QtCore.QRectF(
            margin,
            margin,
            self.width() - 2 * margin,
            self.height() - 2 * margin,
        )
        painter.setPen(QtGui.QPen(QtGui.QColor("#94a3b8"), 1.2))
        painter.setBrush(QtGui.QColor("#ffffff"))
        painter.drawRoundedRect(screen_rect, 10, 10)

        overlay_width, overlay_height, pos_x, pos_y = self._overlay_config
        screen_width = max(1, self._screen_size.width())
        screen_height = max(1, self._screen_size.height())

        width_ratio = min(overlay_width / screen_width, 1.0)
        height_ratio = min(overlay_height / screen_height, 1.0)
        x_ratio = np.clip(pos_x / 100.0, 0.0, 1.0)
        y_ratio = np.clip(pos_y / 100.0, 0.0, 1.0)

        overlay_width_px = max(screen_rect.width() * width_ratio, 6.0)
        overlay_height_px = max(screen_rect.height() * height_ratio, 6.0)

        max_x = screen_rect.width() - overlay_width_px
        max_y = screen_rect.height() - overlay_height_px
        overlay_x = screen_rect.left() + max_x * x_ratio
        overlay_y = screen_rect.top() + max_y * y_ratio

        overlay_rect = QtCore.QRectF(
            overlay_x,
            overlay_y,
            overlay_width_px,
            overlay_height_px,
        )
        painter.setPen(QtGui.QPen(QtGui.QColor("#0f172a"), 1.0))
        painter.setBrush(QtGui.QColor(15, 118, 110, 160))
        painter.drawRoundedRect(overlay_rect, 8, 8)
        painter.end()


class CalibrationOverlayWindow(QtWidgets.QWidget):
    """Full-screen overlay used during gaze calibration."""

    def __init__(self) -> None:
        super().__init__(
            None,
            QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint | QtCore.Qt.Tool,
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
        self._target: Optional[Tuple[float, float]] = None
        self._message: str = ""
        self.hide()

    def set_target(
        self,
        target: Tuple[float, float],
        message: str,
        screen: QtGui.QScreen,
    ) -> None:
        if self.windowHandle():
            self.windowHandle().setScreen(screen)
        geometry = screen.geometry()
        self.setGeometry(geometry)
        self._target = target
        self._message = message
        if not self.isVisible():
            self.showFullScreen()
            self.raise_()
        self.update()

    def clear_target(self) -> None:
        if self._target is None and not self.isVisible():
            return
        self._target = None
        self._message = ""
        self.hide()

    def current_target(self) -> Optional[Tuple[float, float]]:
        return self._target

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:  # noqa: D401
        if not self._target:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(self.rect(), QtGui.QColor(9, 14, 23, 120))
        width = self.width()
        height = self.height()
        tx = int(np.clip(self._target[0], 0.0, 1.0) * width)
        ty = int(np.clip(self._target[1], 0.0, 1.0) * height)

        painter.setPen(QtGui.QPen(QtGui.QColor("#ffba08"), 6))
        painter.setBrush(QtGui.QColor("#ffba08"))
        painter.drawEllipse(QtCore.QPoint(tx, ty), 22, 22)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#2563eb")))
        painter.setPen(QtGui.QPen(QtGui.QColor("#1d4ed8"), 3))
        painter.drawEllipse(QtCore.QPoint(tx, ty), 10, 10)

        if self._message:
            painter.setPen(QtGui.QColor("#e2e8f0"))
            font = painter.font()
            font.setPointSize(28)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(
                QtCore.QRect(0, int(height * 0.1), width, 60),
                QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop,
                self._message,
            )
        painter.end()


class MainWindow(QtWidgets.QMainWindow):
    """Main application window."""

    def __init__(self, config_path: Path) -> None:
        super().__init__()
        self.setWindowTitle("Eye Tracker")
        self.resize(1200, 720)
        self.setStyleSheet(
            """
            QMainWindow { background-color: #f5f7fb; color: #1f2933; }
            QLabel { color: #1f2933; }
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                padding: 8px 12px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #e2e8f0; }
            QPushButton:pressed { background-color: #cbd5e1; }
            QGroupBox {
                border: 1px solid #d0d7e2;
                border-radius: 8px;
                margin-top: 16px;
                padding: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 4px;
            }
            QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 6px;
                background-color: #ffffff;
            }
            QProgressBar {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                text-align: center;
                background: #e2e8f0;
                color: #1f2933;
            }
            QProgressBar::chunk {
                background: #38bdf8;
                border-radius: 6px;
            }
            """
        )

        self._config_path = config_path
        self._calibration_manager = CalibrationManager(config_path)
        self._overlay_window = OverlayWindow()
        self._calibration_overlay = CalibrationOverlayWindow()
        self._tracker = GazeHeadTracker(self._calibration_manager, log_dir=Path("logs"))
        self._head_threshold_spins: dict[str, QtWidgets.QDoubleSpinBox] = {}
        self._gaze_range_spins: dict[str, QtWidgets.QDoubleSpinBox] = {}
        self._overlay_preview = OverlayPreview()
        self._current_calibration_message: str = ""

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QHBoxLayout(central)
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setSpacing(18)

        self._video_widget = VideoWidget()
        layout.addWidget(self._video_widget, alignment=QtCore.Qt.AlignTop)

        self._side_panel = self._build_side_panel()
        self._side_scroll = QtWidgets.QScrollArea()
        self._side_scroll.setWidgetResizable(True)
        self._side_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._side_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._side_scroll.setWidget(self._side_panel)
        self._side_scroll.setMinimumWidth(360)
        layout.addWidget(self._side_scroll, stretch=1)

        self._connect_signals()
        self._overlay_window.hide()
        self._sync_settings_from_manager()
        self._tracker.start()

    def _build_side_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setAlignment(QtCore.Qt.AlignTop)
        panel.setMinimumWidth(340)

        title = QtWidgets.QLabel("Status")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(title)

        self._attention_indicator = QtWidgets.QLabel("Awaiting camera…")
        self._attention_indicator.setStyleSheet("font-size: 18px; color: #1f2933;")
        layout.addWidget(self._attention_indicator)

        self._angles_label = QtWidgets.QLabel("Yaw: ---, Pitch: ---, Roll: ---")
        layout.addWidget(self._angles_label)
        self._gaze_label = QtWidgets.QLabel("Gaze: ---, ---")
        layout.addWidget(self._gaze_label)

        layout.addSpacing(16)
        calibration_title = QtWidgets.QLabel("Calibration")
        calibration_title.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(calibration_title)

        self._calibration_progress = QtWidgets.QProgressBar()
        self._calibration_progress.setRange(0, 100)
        self._calibration_progress.hide()
        layout.addWidget(self._calibration_progress)

        self._calibration_message = QtWidgets.QLabel("")
        self._calibration_message.setWordWrap(True)
        layout.addWidget(self._calibration_message)

        self._head_calibration_btn = QtWidgets.QPushButton("Calibrate Head Pose")
        self._head_calibration_btn.clicked.connect(self._tracker.start_head_pose_calibration)
        layout.addWidget(self._head_calibration_btn)

        self._gaze_calibration_btn = QtWidgets.QPushButton("Calibrate Gaze")
        self._gaze_calibration_btn.clicked.connect(self._tracker.start_gaze_calibration)
        layout.addWidget(self._gaze_calibration_btn)

        self._cancel_calibration_btn = QtWidgets.QPushButton("Cancel Calibration")
        self._cancel_calibration_btn.clicked.connect(self._tracker.cancel_calibration)
        layout.addWidget(self._cancel_calibration_btn)

        layout.addSpacing(16)
        settings_title = QtWidgets.QLabel("Settings")
        settings_title.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(settings_title)

        self._camera_spin = QtWidgets.QSpinBox()
        self._camera_spin.setMinimum(0)
        self._camera_spin.setMaximum(10)
        self._camera_spin.setValue(self._calibration_manager.settings.camera_index)
        self._camera_spin.valueChanged.connect(self._tracker.set_camera_index)
        layout.addWidget(self._create_labeled_widget("Camera index", self._camera_spin))

        self._smoothing_spin = QtWidgets.QSpinBox()
        self._smoothing_spin.setMinimum(1)
        self._smoothing_spin.setMaximum(120)
        self._smoothing_spin.setValue(self._calibration_manager.settings.smoothing_window)
        self._smoothing_spin.valueChanged.connect(self._tracker.set_smoothing_window)
        layout.addWidget(self._create_labeled_widget("Smoothing window", self._smoothing_spin))

        self._warning_spin = QtWidgets.QSpinBox()
        self._warning_spin.setMinimum(1)
        self._warning_spin.setMaximum(120)
        self._warning_spin.setValue(self._calibration_manager.settings.warning_delay_frames)
        self._warning_spin.valueChanged.connect(self._tracker.set_warning_delay)
        layout.addWidget(self._create_labeled_widget("Warning delay (frames)", self._warning_spin))

        self._overlay_checkbox = QtWidgets.QCheckBox("Enable overlay warning")
        self._overlay_checkbox.setChecked(self._calibration_manager.settings.overlay_enabled)
        self._overlay_checkbox.stateChanged.connect(
            lambda state: self._tracker.set_overlay_enabled(state == QtCore.Qt.Checked)
        )
        layout.addWidget(self._overlay_checkbox)

        overlay_group = QtWidgets.QGroupBox("Overlay appearance")
        overlay_group_layout = QtWidgets.QVBoxLayout(overlay_group)
        overlay_form = QtWidgets.QFormLayout()

        self._overlay_width_spin = QtWidgets.QSpinBox()
        self._overlay_width_spin.setRange(160, 800)
        self._overlay_width_spin.setSingleStep(20)
        self._overlay_width_spin.valueChanged.connect(self._on_overlay_config_changed)
        overlay_form.addRow("Width (px)", self._overlay_width_spin)

        self._overlay_height_spin = QtWidgets.QSpinBox()
        self._overlay_height_spin.setRange(80, 400)
        self._overlay_height_spin.setSingleStep(10)
        self._overlay_height_spin.valueChanged.connect(self._on_overlay_config_changed)
        overlay_form.addRow("Height (px)", self._overlay_height_spin)

        self._overlay_pos_x_spin = QtWidgets.QDoubleSpinBox()
        self._overlay_pos_x_spin.setRange(0.0, 100.0)
        self._overlay_pos_x_spin.setSingleStep(1.0)
        self._overlay_pos_x_spin.setSuffix(" %")
        self._overlay_pos_x_spin.valueChanged.connect(self._on_overlay_config_changed)
        overlay_form.addRow("Horizontal position", self._overlay_pos_x_spin)

        self._overlay_pos_y_spin = QtWidgets.QDoubleSpinBox()
        self._overlay_pos_y_spin.setRange(0.0, 100.0)
        self._overlay_pos_y_spin.setSingleStep(1.0)
        self._overlay_pos_y_spin.setSuffix(" %")
        self._overlay_pos_y_spin.valueChanged.connect(self._on_overlay_config_changed)
        overlay_form.addRow("Vertical position", self._overlay_pos_y_spin)

        overlay_group_layout.addLayout(overlay_form)
        preview_label = QtWidgets.QLabel("Overlay preview")
        preview_label.setAlignment(QtCore.Qt.AlignCenter)
        overlay_group_layout.addWidget(preview_label)
        overlay_group_layout.addWidget(self._overlay_preview, alignment=QtCore.Qt.AlignCenter)
        layout.addWidget(overlay_group)

        head_threshold_group = QtWidgets.QGroupBox("Head pose thresholds (degrees)")
        head_form = QtWidgets.QFormLayout(head_threshold_group)
        for axis in ("yaw", "pitch", "roll"):
            spin = QtWidgets.QDoubleSpinBox()
            spin.setRange(1.0, 60.0)
            spin.setSingleStep(1.0)
            spin.valueChanged.connect(self._on_head_threshold_changed)
            head_form.addRow(axis.capitalize(), spin)
            self._head_threshold_spins[axis] = spin
        layout.addWidget(head_threshold_group)

        gaze_threshold_group = QtWidgets.QGroupBox("Gaze thresholds (normalised)")
        gaze_form = QtWidgets.QFormLayout(gaze_threshold_group)
        for key, label in (
            ("horizontal_min", "Horizontal min"),
            ("horizontal_max", "Horizontal max"),
            ("vertical_min", "Vertical min"),
            ("vertical_max", "Vertical max"),
        ):
            spin = QtWidgets.QDoubleSpinBox()
            spin.setRange(-1.0, 1.0)
            spin.setSingleStep(0.01)
            spin.valueChanged.connect(self._on_gaze_threshold_changed)
            gaze_form.addRow(label, spin)
            self._gaze_range_spins[key] = spin
        layout.addWidget(gaze_threshold_group)

        layout.addStretch(1)

        return panel

    def _create_labeled_widget(self, label: str, widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget()
        h_layout = QtWidgets.QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        text_label = QtWidgets.QLabel(label)
        h_layout.addWidget(text_label)
        h_layout.addWidget(widget)
        return container

    def _connect_signals(self) -> None:
        self._tracker.frame_ready.connect(self._on_frame_ready)
        self._tracker.status_updated.connect(self._on_status_update)
        self._tracker.calibration_step.connect(self._on_calibration_step)
        self._tracker.calibration_finished.connect(self._on_calibration_finished)
        self._tracker.warning_state_changed.connect(self._on_warning_state)
        self._tracker.error_occurred.connect(self._on_error)

    def _on_frame_ready(self, frame: np.ndarray, payload: Dict) -> None:
        landmarks = payload.get("landmarks")
        target = payload.get("calibration_target")
        head_angles = payload.get("head_angles")
        gaze_vector = payload.get("gaze_vector")
        iris_positions = payload.get("iris_positions")
        self._video_widget.set_frame(frame, landmarks, head_angles, gaze_vector, iris_positions)
        if target:
            screen = self.screen() or QtGui.QGuiApplication.primaryScreen()
            if screen:
                self._calibration_overlay.set_target(target, self._current_calibration_message, screen)
        else:
            self._calibration_overlay.clear_target()

    def _on_status_update(self, payload: Dict) -> None:
        head_angles: Optional[Tuple[float, float, float]] = payload.get("head_angles")
        gaze_vector: Optional[Tuple[float, float]] = payload.get("gaze_vector")
        head_pose_within = payload.get("head_pose_within")
        gaze_within = payload.get("gaze_within")
        attention_ok = payload.get("attention_ok")

        if head_angles:
            self._angles_label.setText(
                "Head yaw (left/right): "
                f"{head_angles[0]:+.1f} deg\n"
                "Head pitch (up/down): "
                f"{head_angles[1]:+.1f} deg\n"
                "Head roll (tilt): "
                f"{head_angles[2]:+.1f} deg"
            )
        else:
            self._angles_label.setText("Head yaw/pitch/roll: (awaiting data)")

        if gaze_vector:
            self._gaze_label.setText(
                "Gaze horizontal (left/right): "
                f"{gaze_vector[0]:+.2f}\n"
                "Gaze vertical (up/down): "
                f"{gaze_vector[1]:+.2f}"
            )
        else:
            self._gaze_label.setText("Gaze horizontal/vertical: (awaiting data)")

        if attention_ok:
            self._attention_indicator.setText("Paying attention")
            self._attention_indicator.setStyleSheet("color: #2e7d32; font-size: 18px;")
        else:
            self._attention_indicator.setText("Attention warning")
            self._attention_indicator.setStyleSheet("color: #c62828; font-size: 18px;")

    def _on_calibration_step(self, message: str, progress: int, total: int) -> None:
        if total > 0:
            percent = int((progress / total) * 100)
            self._calibration_progress.setRange(0, 100)
            self._calibration_progress.setValue(percent)
            self._calibration_progress.show()
        self._current_calibration_message = message
        self._calibration_message.setText(message)
        if self._calibration_overlay.isVisible():
            screen = self.screen() or QtGui.QGuiApplication.primaryScreen()
            current_target = self._calibration_overlay.current_target()
            if screen and current_target:
                self._calibration_overlay.set_target(
                    current_target,
                    self._current_calibration_message,
                    screen,
                )

    def _on_calibration_finished(self, message: str) -> None:
        self._calibration_message.setText(message)
        self._calibration_progress.hide()
        self._calibration_progress.setValue(0)
        self._current_calibration_message = ""
        self._calibration_overlay.clear_target()
        self._sync_settings_from_manager()

    def _on_warning_state(self, active: bool, message: str) -> None:
        if self._overlay_checkbox.isChecked():
            self._overlay_window.set_message(message if active else "")
        else:
            self._overlay_window.set_message("")

    def _on_error(self, message: str) -> None:
        """Show error dialog with retry option."""
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setIcon(QtWidgets.QMessageBox.Critical)
        msg_box.setWindowTitle("Camera Error")
        msg_box.setText(message)
        msg_box.setInformativeText("Would you like to retry?")
        
        retry_button = msg_box.addButton("Retry", QtWidgets.QMessageBox.AcceptRole)
        cancel_button = msg_box.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == retry_button:
            self._tracker.retry_camera()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: D401
        self._tracker.stop()
        self._overlay_window.close()
        self._calibration_overlay.close()
        super().closeEvent(event)

    def _sync_settings_from_manager(self) -> None:
        settings = self._calibration_manager.settings
        with QtCore.QSignalBlocker(self._camera_spin):
            self._camera_spin.setValue(settings.camera_index)
        with QtCore.QSignalBlocker(self._smoothing_spin):
            self._smoothing_spin.setValue(settings.smoothing_window)
        with QtCore.QSignalBlocker(self._warning_spin):
            self._warning_spin.setValue(settings.warning_delay_frames)
        with QtCore.QSignalBlocker(self._overlay_checkbox):
            self._overlay_checkbox.setChecked(settings.overlay_enabled)
        with QtCore.QSignalBlocker(self._overlay_width_spin):
            self._overlay_width_spin.setValue(settings.overlay_width)
        with QtCore.QSignalBlocker(self._overlay_height_spin):
            self._overlay_height_spin.setValue(settings.overlay_height)
        with QtCore.QSignalBlocker(self._overlay_pos_x_spin):
            self._overlay_pos_x_spin.setValue(settings.overlay_pos_x)
        with QtCore.QSignalBlocker(self._overlay_pos_y_spin):
            self._overlay_pos_y_spin.setValue(settings.overlay_pos_y)
        self._apply_overlay_settings(
            settings.overlay_width,
            settings.overlay_height,
            settings.overlay_pos_x,
            settings.overlay_pos_y,
        )

        calibration = self._calibration_manager.calibration
        thresholds = calibration.head_pose.thresholds
        for idx, axis in enumerate(("yaw", "pitch", "roll")):
            spin = self._head_threshold_spins.get(axis)
            if spin:
                with QtCore.QSignalBlocker(spin):
                    spin.setValue(thresholds[idx])

        gaze = calibration.gaze
        values = {
            "horizontal_min": gaze.horizontal_range[0],
            "horizontal_max": gaze.horizontal_range[1],
            "vertical_min": gaze.vertical_range[0],
            "vertical_max": gaze.vertical_range[1],
        }
        for key, value in values.items():
            spin = self._gaze_range_spins.get(key)
            if spin:
                with QtCore.QSignalBlocker(spin):
                    spin.setValue(value)

    def _on_head_threshold_changed(self) -> None:
        thresholds = tuple(self._head_threshold_spins[axis].value() for axis in ("yaw", "pitch", "roll"))
        self._calibration_manager.update_head_pose_thresholds(thresholds)  # type: ignore[arg-type]

    def _on_gaze_threshold_changed(self) -> None:
        horizontal = (
            self._gaze_range_spins["horizontal_min"].value(),
            self._gaze_range_spins["horizontal_max"].value(),
        )
        vertical = (
            self._gaze_range_spins["vertical_min"].value(),
            self._gaze_range_spins["vertical_max"].value(),
        )
        self._calibration_manager.update_gaze_ranges(horizontal, vertical)  # type: ignore[arg-type]

    def _on_overlay_config_changed(self) -> None:
        width = self._overlay_width_spin.value()
        height = self._overlay_height_spin.value()
        pos_x = self._overlay_pos_x_spin.value()
        pos_y = self._overlay_pos_y_spin.value()
        self._calibration_manager.update_settings(
            overlay_width=width,
            overlay_height=height,
            overlay_pos_x=pos_x,
            overlay_pos_y=pos_y,
        )
        self._apply_overlay_settings(width, height, pos_x, pos_y)

    def _apply_overlay_settings(self, width: int, height: int, pos_x: float, pos_y: float) -> None:
        self._overlay_window.configure(width, height, pos_x, pos_y)
        screen = QtGui.QGuiApplication.primaryScreen()
        screen_size = screen.availableGeometry().size() if screen else QtCore.QSize(width, height)
        self._overlay_preview.update_preview(screen_size, width, height, pos_x, pos_y)


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    
    # Handle both running as script and as PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = Path(sys._MEIPASS)
    else:
        # Running as script
        application_path = Path(__file__).resolve().parent
    
    config_path = application_path / "config.json"
    window = MainWindow(config_path)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

