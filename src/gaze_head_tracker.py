"""Real-time gaze and head pose tracking using MediaPipe and OpenCV."""

from __future__ import annotations

import csv
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np
from PySide6 import QtCore

try:
    from .calibration import CalibrationManager
    from .utils import MovingAverageFilter, rotation_vector_to_euler
except ImportError:
    from calibration import CalibrationManager
    from utils import MovingAverageFilter, rotation_vector_to_euler


HEAD_POSE_SAMPLE_COUNT = 60
GAZE_CALIBRATION_STEPS = [
    ("Focus on the centre of the screen", "center", (0.5, 0.5)),
    ("Focus on the top-left corner", "top_left", (0.1, 0.1)),
    ("Focus on the top-right corner", "top_right", (0.9, 0.1)),
    ("Focus on the bottom-left corner", "bottom_left", (0.1, 0.9)),
    ("Focus on the bottom-right corner", "bottom_right", (0.9, 0.9)),
]
GAZE_SAMPLES_PER_STEP = 45

LEFT_IRIS_LANDMARKS = [468, 469, 470, 471, 472]
RIGHT_IRIS_LANDMARKS = [473, 474, 475, 476, 477]

MODEL_3D_POINTS = np.array(
    [
        (0.0, 0.0, 0.0),  # Nose tip
        (0.0, -63.6, -12.5),  # Chin
        (-43.3, 32.7, -26.0),  # Left eye left corner
        (43.3, 32.7, -26.0),  # Right eye right corner
        (-28.9, -28.9, -24.1),  # Left mouth corner
        (28.9, -28.9, -24.1),  # Right mouth corner
    ],
    dtype=np.float32,
)

FACE_LANDMARK_INDICES = [1, 152, 263, 33, 291, 61]


@dataclass
class TrackingResult:
    """Container for per-frame tracking outputs."""

    frame: np.ndarray
    landmarks: Optional[List[Tuple[float, float]]] = None
    head_angles: Optional[Tuple[float, float, float]] = None
    gaze_vector: Optional[Tuple[float, float]] = None
    iris_positions: Optional[Tuple[Tuple[float, float], Tuple[float, float]]] = None
    head_pose_within: bool = False
    gaze_within: bool = False
    attention_ok: bool = False


class GazeHeadTracker(QtCore.QObject):
    """Background worker that captures video frames and computes gaze metrics."""

    frame_ready = QtCore.Signal(np.ndarray, dict)
    status_updated = QtCore.Signal(dict)
    calibration_step = QtCore.Signal(str, int, int)
    calibration_finished = QtCore.Signal(str)
    warning_state_changed = QtCore.Signal(bool, str)
    error_occurred = QtCore.Signal(str)

    def __init__(self, calibration_manager: CalibrationManager, log_dir: Optional[Path] = None) -> None:
        super().__init__()
        self._calibration_manager = calibration_manager
        self._log_dir = log_dir
        self._capture: Optional[cv2.VideoCapture] = None
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_tracking_confidence=0.5,
            min_detection_confidence=0.5,
        )

        smoothing_window = calibration_manager.settings.smoothing_window
        self._head_filter = MovingAverageFilter(window_size=smoothing_window)
        self._gaze_filter = MovingAverageFilter(window_size=smoothing_window)

        self._latest_result: Optional[TrackingResult] = None
        self._frames_outside_threshold = 0

        self._calibration_mode: Optional[str] = None
        self._head_pose_samples: List[Tuple[float, float, float]] = []
        self._gaze_samples: Dict[str, List[Tuple[float, float]]] = {}
        self._current_step_index = 0
        self._current_target: Optional[Tuple[float, float]] = None

        self._csv_writer: Optional[csv.writer] = None
        self._csv_file_handle = None

    def start(self) -> None:
        """Start the capture loop in a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop capture and release resources."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._release_resources()

    def _release_resources(self) -> None:
        if self._capture and self._capture.isOpened():
            self._capture.release()
        if self._csv_file_handle:
            self._csv_file_handle.close()
            self._csv_file_handle = None
            self._csv_writer = None

    def _ensure_capture(self) -> bool:
        if self._capture and self._capture.isOpened():
            return True
        index = self._calibration_manager.settings.camera_index
        self._capture = cv2.VideoCapture(index, cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else 0)
        width = self._calibration_manager.settings.frame_width
        height = self._calibration_manager.settings.frame_height
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self._capture.isOpened():
            self.error_occurred.emit(f"Unable to open camera index {index}")
            return False
        return True

    def _capture_loop(self) -> None:
        """Read frames until stop event triggers."""
        warning_message = ""
        warning_active = False
        last_emit = time.time()
        fps_limit = 1.0 / 30.0

        if self._calibration_manager.settings.log_to_csv and self._log_dir:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            csv_path = self._log_dir / "tracking_log.csv"
            self._csv_file_handle = csv_path.open("w", newline="", encoding="utf-8")
            self._csv_writer = csv.writer(self._csv_file_handle)
            self._csv_writer.writerow(["timestamp", "yaw", "pitch", "roll", "gaze_horizontal", "gaze_vertical"])

        while not self._stop_event.is_set():
            if not self._ensure_capture():
                time.sleep(1.0)
                continue

            ret, frame = self._capture.read()
            if not ret:
                self.error_occurred.emit("Failed to read frame from camera.")
                time.sleep(0.5)
                continue

            result = self._process_frame(frame)
            self._latest_result = result

            current_time = time.time()
            if current_time - last_emit >= fps_limit:
                last_emit = current_time
                if result:
                    self.frame_ready.emit(result.frame, self._result_to_payload(result))

            if result.head_pose_within and result.gaze_within:
                self._frames_outside_threshold = 0
            else:
                self._frames_outside_threshold += 1

            if self._calibration_mode:
                warning_message = ""
                warning_active = False
            else:
                warning_delay = self._calibration_manager.settings.warning_delay_frames
                if self._frames_outside_threshold >= warning_delay:
                    warning_message = "Please look at the screen."
                    warning_active = True
                else:
                    warning_message = ""
                    warning_active = False

            self._emit_status(result, warning_active, warning_message)
            time.sleep(0.001)

        self._release_resources()

    def _emit_status(self, result: TrackingResult, warning_active: bool, message: str) -> None:
        payload = self._result_to_payload(result)
        payload["warning_active"] = warning_active
        payload["warning_message"] = message
        self.status_updated.emit(payload)
        self.warning_state_changed.emit(warning_active, message)

    def _result_to_payload(self, result: TrackingResult) -> Dict:
        payload: Dict = {
            "head_angles": result.head_angles,
            "gaze_vector": result.gaze_vector,
            "iris_positions": result.iris_positions,
            "head_pose_within": result.head_pose_within,
            "gaze_within": result.gaze_within,
            "attention_ok": result.attention_ok,
            "landmarks": result.landmarks,
            "calibration_target": self._current_target,
        }
        return payload

    def _process_frame(self, frame: np.ndarray) -> TrackingResult:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._face_mesh.process(rgb_frame)
        track_result = TrackingResult(frame=frame)

        if not results.multi_face_landmarks:
            return track_result

        face_landmarks = results.multi_face_landmarks[0]
        image_rows, image_cols, _ = frame.shape
        track_result.landmarks = [
            (int(lm.x * image_cols), int(lm.y * image_rows)) for lm in face_landmarks.landmark
        ]
        points_2d = []
        for idx in FACE_LANDMARK_INDICES:
            landmark = face_landmarks.landmark[idx]
            point = (landmark.x * image_cols, landmark.y * image_rows)
            points_2d.append(point)
        if len(points_2d) != len(MODEL_3D_POINTS):
            return track_result

        points_2d_np = np.array(points_2d, dtype=np.float32)
        focal_length = image_cols
        camera_matrix = np.array(
            [[focal_length, 0, image_cols / 2], [0, focal_length, image_rows / 2], [0, 0, 1]],
            dtype=np.float32,
        )
        dist_coeffs = np.zeros((4, 1), dtype=np.float32)

        success, rotation_vec, _ = cv2.solvePnP(
            MODEL_3D_POINTS,
            points_2d_np,
            camera_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not success:
            return track_result

        yaw, pitch, roll = rotation_vector_to_euler(rotation_vec)
        smoothed_angles = tuple(self._head_filter.add([yaw, pitch, roll]))
        track_result.head_angles = smoothed_angles

        head_pose_within = self._calibration_manager.calibration.head_pose.within_threshold(smoothed_angles)
        track_result.head_pose_within = head_pose_within

        gaze_data = self._compute_gaze_vector(face_landmarks, frame)
        if gaze_data is not None:
            gaze_vector, iris_positions = gaze_data
            smoothed_gaze = tuple(self._gaze_filter.add(gaze_vector))
            track_result.gaze_vector = smoothed_gaze
            track_result.iris_positions = iris_positions
            gaze_within = self._calibration_manager.calibration.gaze.within_threshold(smoothed_gaze)
            track_result.gaze_within = gaze_within
        else:
            track_result.gaze_vector = None
            track_result.iris_positions = None
            track_result.gaze_within = False

        track_result.attention_ok = track_result.head_pose_within and track_result.gaze_within

        self._handle_calibration_updates(track_result)
        self._log_result(track_result)
        return track_result

    def _compute_gaze_vector(
        self, landmarks, frame: np.ndarray
    ) -> Optional[Tuple[Tuple[float, float], Tuple[Tuple[float, float], Tuple[float, float]]]]:
        height, width, _ = frame.shape

        def landmark_xy_pixels(index: int) -> np.ndarray:
            lm = landmarks.landmark[index]
            return np.array([lm.x * width, lm.y * height], dtype=np.float32)

        left_center = self._estimate_iris_center(LEFT_IRIS_LANDMARKS, landmarks, width, height)
        right_center = self._estimate_iris_center(RIGHT_IRIS_LANDMARKS, landmarks, width, height)

        left_eye_coords = [landmark_xy_pixels(idx) for idx in (33, 133)]
        right_eye_coords = [landmark_xy_pixels(idx) for idx in (362, 263)]

        def compute_vector(eye_center, eye_corner_pair):
            if eye_center is None:
                return None
            eye_start = eye_corner_pair[0]
            eye_end = eye_corner_pair[1]
            eye_center_ref = (eye_start + eye_end) / 2.0
            eye_width = np.linalg.norm(eye_end - eye_start)
            eye_height = abs(eye_corner_pair[0][1] - eye_corner_pair[1][1]) + 1e-5
            vector = np.array(eye_center) - eye_center_ref
            horizontal = vector[0] / (eye_width + 1e-5)
            vertical = vector[1] / (eye_height + 1e-5)
            return horizontal, vertical

        left_vector = compute_vector(left_center, left_eye_coords)
        right_vector = compute_vector(right_center, right_eye_coords)

        vectors = [vec for vec in (left_vector, right_vector) if vec is not None]
        if not vectors:
            return None
        mean_vector = np.mean(vectors, axis=0)
        gaze_vector = (float(mean_vector[0]), float(mean_vector[1]))
        
        iris_positions = None
        if left_center is not None and right_center is not None:
            iris_positions = (
                (float(left_center[0]), float(left_center[1])),
                (float(right_center[0]), float(right_center[1])),
            )
        
        return gaze_vector, iris_positions

    def _estimate_iris_center(
        self,
        indices: List[int],
        face_landmarks,
        frame_width: int,
        frame_height: int,
    ) -> Optional[np.ndarray]:
        pts = []
        for idx in indices:
            landmark = face_landmarks.landmark[idx]
            pts.append((landmark.x, landmark.y))
        if not pts:
            return None
        pts_np = np.array(pts, dtype=np.float32)
        center = np.mean(pts_np, axis=0)
        return np.array([center[0] * frame_width, center[1] * frame_height], dtype=np.float32)

    def _handle_calibration_updates(self, result: TrackingResult) -> None:
        if not self._calibration_mode:
            return

        if self._calibration_mode == "head_pose":
            if result.head_angles:
                self._head_pose_samples.append(result.head_angles)
                self.calibration_step.emit(
                    "Collecting head pose baseline…",
                    min(len(self._head_pose_samples), HEAD_POSE_SAMPLE_COUNT),
                    HEAD_POSE_SAMPLE_COUNT,
                )
            if len(self._head_pose_samples) >= HEAD_POSE_SAMPLE_COUNT:
                averages = np.mean(self._head_pose_samples, axis=0)
                self._calibration_manager.update_head_pose_baseline(tuple(float(x) for x in averages))
                self._head_filter.reset()
                self._head_pose_samples.clear()
                self._calibration_mode = None
                self.calibration_finished.emit("Head pose calibration completed.")

        elif self._calibration_mode == "gaze":
            if not result.gaze_vector:
                return
            instruction, step_key, target = GAZE_CALIBRATION_STEPS[self._current_step_index]
            samples = self._gaze_samples.setdefault(step_key, [])
            samples.append(result.gaze_vector)
            self._current_target = target
            self.calibration_step.emit(
                instruction,
                min(len(samples), GAZE_SAMPLES_PER_STEP),
                GAZE_SAMPLES_PER_STEP,
            )
            if len(samples) >= GAZE_SAMPLES_PER_STEP:
                self._current_step_index += 1
                if self._current_step_index >= len(GAZE_CALIBRATION_STEPS):
                    self._finalise_gaze_calibration()
                else:
                    next_instruction, _, next_target = GAZE_CALIBRATION_STEPS[self._current_step_index]
                    self._current_target = next_target
                    self.calibration_step.emit(next_instruction, 0, GAZE_SAMPLES_PER_STEP)

    def _finalise_gaze_calibration(self) -> None:
        horizontal_values = []
        vertical_values = []
        for samples in self._gaze_samples.values():
            horizontal_values.extend([sample[0] for sample in samples])
            vertical_values.extend([sample[1] for sample in samples])
        if horizontal_values and vertical_values:
            horizontal_min = float(min(horizontal_values))
            horizontal_max = float(max(horizontal_values))
            vertical_min = float(min(vertical_values))
            vertical_max = float(max(vertical_values))

            margin = 0.05
            self._calibration_manager.update_gaze_ranges(
                (horizontal_min - margin, horizontal_max + margin),
                (vertical_min - margin, vertical_max + margin),
            )
        self._gaze_filter.reset()
        self._gaze_samples.clear()
        self._calibration_mode = None
        self._current_step_index = 0
        self._current_target = None
        self.calibration_finished.emit("Gaze calibration completed.")

    def start_head_pose_calibration(self) -> None:
        self._calibration_mode = "head_pose"
        self._head_pose_samples.clear()
        self._current_target = None
        self.calibration_step.emit("Hold your head in a neutral position", 0, HEAD_POSE_SAMPLE_COUNT)

    def start_gaze_calibration(self) -> None:
        self._calibration_mode = "gaze"
        self._gaze_samples.clear()
        self._current_step_index = 0
        instruction, _, target = GAZE_CALIBRATION_STEPS[0]
        self._current_target = target
        self.calibration_step.emit(instruction, 0, GAZE_SAMPLES_PER_STEP)

    def cancel_calibration(self) -> None:
        self._calibration_mode = None
        self._head_pose_samples.clear()
        self._gaze_samples.clear()
        self._current_step_index = 0
        self._current_target = None
        self.calibration_finished.emit("Calibration cancelled.")

    def set_camera_index(self, index: int) -> None:
        self._calibration_manager.update_settings(camera_index=index)
        if self._capture and self._capture.isOpened():
            self._capture.release()

    def set_overlay_enabled(self, enabled: bool) -> None:
        self._calibration_manager.update_settings(overlay_enabled=bool(enabled))

    def set_warning_delay(self, delay_frames: int) -> None:
        delay_frames = int(max(1, delay_frames))
        self._calibration_manager.update_settings(warning_delay_frames=delay_frames)

    def set_smoothing_window(self, window_size: int) -> None:
        window_size = max(1, int(window_size))
        self._calibration_manager.update_settings(smoothing_window=window_size)
        self._head_filter = MovingAverageFilter(window_size=window_size)
        self._gaze_filter = MovingAverageFilter(window_size=window_size)

    def _log_result(self, result: TrackingResult) -> None:
        if not self._csv_writer:
            return
        if not result.head_angles or not result.gaze_vector:
            return
        self._csv_writer.writerow(
            [
                time.time(),
                result.head_angles[0],
                result.head_angles[1],
                result.head_angles[2],
                result.gaze_vector[0],
                result.gaze_vector[1],
            ]
        )

