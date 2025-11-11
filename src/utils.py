"""Utility helpers for gaze and head tracking."""

from __future__ import annotations

import json
import math
import threading
from collections import deque
from pathlib import Path
from typing import Deque, Dict, Iterable, List, Optional, Tuple

import cv2
import numpy as np


class MovingAverageFilter:
    """Simple moving average filter for scalar or vector values."""

    def __init__(self, window_size: int = 5) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        self.window_size = window_size
        self._buffer: Deque[np.ndarray] = deque(maxlen=window_size)
        self._lock = threading.Lock()

    def reset(self) -> None:
        """Reset the buffer."""
        with self._lock:
            self._buffer.clear()

    def add(self, value: Iterable[float]) -> np.ndarray:
        """Add a value and return the current average."""
        array = np.array(value, dtype=np.float32)
        with self._lock:
            self._buffer.append(array)
            stacked = np.stack(self._buffer, axis=0)
        return np.mean(stacked, axis=0)


def rotation_vector_to_euler(rvec: np.ndarray) -> Tuple[float, float, float]:
    """Convert a rotation vector to yaw, pitch, roll in degrees."""
    rotation_matrix, _ = cv2.Rodrigues(rvec)
    sy = math.sqrt(rotation_matrix[0, 0] ** 2 + rotation_matrix[1, 0] ** 2)
    singular = sy < 1e-6
    if not singular:
        pitch = math.atan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
        yaw = math.atan2(-rotation_matrix[2, 0], sy)
        roll = math.atan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
    else:
        pitch = math.atan2(-rotation_matrix[1, 2], rotation_matrix[1, 1])
        yaw = math.atan2(-rotation_matrix[2, 0], sy)
        roll = 0.0
    return (
        math.degrees(yaw),
        math.degrees(pitch),
        math.degrees(roll),
    )


def load_json(path: Path, default: Optional[Dict] = None) -> Dict:
    """Load JSON data from a file or return default."""
    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return default.copy() if default else {}
    except json.JSONDecodeError:
        return default.copy() if default else {}


def save_json(path: Path, data: Dict) -> None:
    """Persist JSON data atomically."""
    tmp_path = Path(f"{path}.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    tmp_path.replace(path)


def clamp(value: float, lower: float, upper: float) -> float:
    """Clamp a value to the provided range."""
    return max(lower, min(value, upper))


def normalise_vector(vec: np.ndarray) -> np.ndarray:
    """Normalise a vector, returning zero vector if magnitude is 0."""
    norm = np.linalg.norm(vec)
    if norm == 0:
        return np.zeros_like(vec)
    return vec / norm


def compute_eye_roi(landmarks: List[Tuple[float, float]], scale: Tuple[int, int]) -> Tuple[int, int, int, int]:
    """Compute bounding box for an eye based on landmarks."""
    width, height = scale
    xs = [int(landmark[0] * width) for landmark in landmarks]
    ys = [int(landmark[1] * height) for landmark in landmarks]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    padding_w = max(1, (max_x - min_x) // 4)
    padding_h = max(1, (max_y - min_y) // 4)
    return (
        max(0, min_x - padding_w),
        max(0, min_y - padding_h),
        min(width, max_x + padding_w),
        min(height, max_y + padding_h),
    )

