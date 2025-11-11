# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Get MediaPipe package location
import mediapipe
mp_dir = Path(mediapipe.__file__).parent

# Collect all MediaPipe data files
mp_data = []
for root, dirs, files in os.walk(str(mp_dir)):
    for file in files:
        if file.endswith(('.binarypb', '.tflite', '.task')):
            src_path = os.path.join(root, file)
            rel_path = os.path.relpath(src_path, str(mp_dir.parent))
            dest_dir = os.path.dirname(rel_path)
            mp_data.append((src_path, dest_dir))

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src\\config.json', '.'),
        ('src\\calibration.py', '.'),
        ('src\\gaze_head_tracker.py', '.'),
        ('src\\overlay.py', '.'),
        ('src\\utils.py', '.'),
    ] + mp_data,
    hiddenimports=[
        'mediapipe',
        'mediapipe.python',
        'mediapipe.python.solutions',
        'mediapipe.python.solutions.face_mesh',
        'mediapipe.python.solution_base',
        'cv2',
        'numpy',
        'scipy',
        'scipy.spatial',
        'scipy.spatial.transform',
        'scipy.spatial.transform._rotation',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

# One-file executable configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='EyeTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
