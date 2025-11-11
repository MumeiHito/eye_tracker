"""PyInstaller hook for MediaPipe package."""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all MediaPipe data files
datas = collect_data_files('mediapipe')

# Collect all MediaPipe submodules
hiddenimports = collect_submodules('mediapipe')

