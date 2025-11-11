"""Calibration data management for gaze and head pose tracking."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np

try:
    from .utils import load_json, save_json
except ImportError:
    from utils import load_json, save_json


@dataclass
class HeadPoseCalibration:
    """Baseline angles and thresholds for head pose deviation."""

    baseline: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    thresholds: Tuple[float, float, float] = (15.0, 15.0, 15.0)  # yaw, pitch, roll

    def within_threshold(self, angles: Tuple[float, float, float]) -> bool:
        """Return True if angles are within thresholds from baseline."""
        diffs = np.abs(np.array(angles) - np.array(self.baseline))
        return bool(np.all(diffs <= np.array(self.thresholds)))


@dataclass
class GazeCalibration:
    """Threshold ranges for gaze estimation."""

    horizontal_range: Tuple[float, float] = (-0.3, 0.3)
    vertical_range: Tuple[float, float] = (-0.3, 0.3)

    def within_threshold(self, gaze_vector: Tuple[float, float]) -> bool:
        """Return True if gaze vector components fall within ranges."""
        horizontal, vertical = gaze_vector
        return (
            self.horizontal_range[0] <= horizontal <= self.horizontal_range[1]
            and self.vertical_range[0] <= vertical <= self.vertical_range[1]
        )


@dataclass
class CalibrationData:
    """Combined calibration state."""

    head_pose: HeadPoseCalibration = field(default_factory=HeadPoseCalibration)
    gaze: GazeCalibration = field(default_factory=GazeCalibration)

    def to_dict(self) -> Dict:
        """Convert to serialisable dictionary."""
        return {
            "head_pose": {
                "baseline": list(self.head_pose.baseline),
                "thresholds": list(self.head_pose.thresholds),
            },
            "gaze": {
                "horizontal_range": list(self.gaze.horizontal_range),
                "vertical_range": list(self.gaze.vertical_range),
            },
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "CalibrationData":
        """Create calibration data from dictionary."""
        head_pose_data = data.get("head_pose", {})
        gaze_data = data.get("gaze", {})
        head_pose = HeadPoseCalibration(
            baseline=tuple(head_pose_data.get("baseline", (0.0, 0.0, 0.0))),
            thresholds=tuple(head_pose_data.get("thresholds", (15.0, 15.0, 15.0))),
        )
        gaze = GazeCalibration(
            horizontal_range=tuple(gaze_data.get("horizontal_range", (-0.3, 0.3))),
            vertical_range=tuple(gaze_data.get("vertical_range", (-0.3, 0.3))),
        )
        return cls(head_pose=head_pose, gaze=gaze)


@dataclass
class Settings:
    """User-adjustable settings."""

    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    smoothing_window: int = 5
    warning_delay_frames: int = 10
    overlay_enabled: bool = True
    log_to_csv: bool = False
    overlay_width: int = 360
    overlay_height: int = 140
    overlay_pos_x: float = 50.0  # percentage of available width
    overlay_pos_y: float = 12.0  # percentage of available height

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Settings":
        return cls(
            camera_index=int(data.get("camera_index", 0)),
            frame_width=int(data.get("frame_width", 640)),
            frame_height=int(data.get("frame_height", 480)),
            smoothing_window=int(data.get("smoothing_window", 5)),
            warning_delay_frames=int(data.get("warning_delay_frames", 10)),
            overlay_enabled=bool(data.get("overlay_enabled", True)),
            log_to_csv=bool(data.get("log_to_csv", False)),
            overlay_width=int(data.get("overlay_width", 360)),
            overlay_height=int(data.get("overlay_height", 140)),
            overlay_pos_x=float(data.get("overlay_pos_x", 50.0)),
            overlay_pos_y=float(data.get("overlay_pos_y", 12.0)),
        )


class CalibrationManager:
    """Manage calibration and settings persistence."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.calibration = CalibrationData()
        self.settings = Settings()
        self._load()

    def _load(self) -> None:
        data = load_json(self.config_path, default={})
        if not data:
            return
        calibration_data = data.get("calibration", {})
        settings_data = data.get("settings", {})
        self.calibration = CalibrationData.from_dict(calibration_data)
        self.settings = Settings.from_dict(settings_data)

    def save(self) -> None:
        payload = {
            "settings": self.settings.to_dict(),
            "calibration": self.calibration.to_dict(),
        }
        save_json(self.config_path, payload)

    def update_head_pose_baseline(self, angles: Tuple[float, float, float]) -> None:
        self.calibration.head_pose.baseline = tuple(angles)
        self.save()

    def update_head_pose_thresholds(self, thresholds: Tuple[float, float, float]) -> None:
        self.calibration.head_pose.thresholds = tuple(thresholds)
        self.save()

    def update_gaze_ranges(
        self, horizontal_range: Tuple[float, float], vertical_range: Tuple[float, float]
    ) -> None:
        self.calibration.gaze.horizontal_range = tuple(horizontal_range)
        self.calibration.gaze.vertical_range = tuple(vertical_range)
        self.save()

    def update_settings(self, **kwargs) -> None:
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self.save()

    def reset(self) -> None:
        self.calibration = CalibrationData()
        self.settings = Settings()
        self.save()

