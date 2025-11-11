# Eye Tracker デスクトップアプリケーション

[English](README.md) | [日本語](README.ja.md)

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

単一のウェブカメラを使用して頭部姿勢と視線を監視するクロスプラットフォームデスクトップアプリケーション（WindowsおよびmacOS対応）。ユーザーが画面から目を離したことを検出し、常に最前面に表示される通知オーバーレイを表示します。

## スクリーンショット

*ライブカメラフィードとリアルタイム顔追跡を備えたアプリケーション*

## 目次

- [機能](#機能)
- [要件](#要件)
- [クイックスタート](#クイックスタート)
- [キャリブレーションワークフロー](#キャリブレーションワークフロー)
- [コントロールと設定](#コントロールと設定)
- [PyInstallerによるパッケージング](#pyinstallerによるパッケージング)
- [貢献](#貢献)
- [ライセンス](#ライセンス)

## 機能

- リアルタイムウェブカメラキャプチャ（OpenCV）とMediaPipeフェイスメッシュ・虹彩検出
- `solvePnP`による頭部姿勢推定と設定可能なスムージング
- 画面中央と端の誘導キャリブレーション付き視線ベクトル計算
- 永続的なキャリブレーションデータとアプリケーション設定（`src/config.json`）
- ライブビデオプレビュー、オーバーレイ、キャリブレーションコントロール付きPySide6 GUI
- 注意力低下時に警告する透明オーバーレイウィンドウ
- デバッグまたは分析用のオプションCSVロギング
- スタンドアロン実行可能ファイル用PyInstallerパッケージング設定

## 要件

- Python 3.12
- オペレーティングシステムからアクセス可能なウェブカメラ
- Windows 10以降またはmacOS 12以降（手動テスト済み）

Python依存関係は`requirements.txt`に記載されています（MediaPipe、OpenCV、PySide6、NumPy、SciPy、PyInstaller）。

## クイックスタート

1. **プロジェクトのクローンとディレクトリ移動**

   ```bash
   git clone <repo-url> eye_tracker
   cd eye_tracker
   ```

2. **仮想環境の作成と有効化（Python 3.12）**

   - macOS / Linux:

     ```bash
     python3.12 -m venv venv
     source venv/bin/activate
     ```

   - Windows (PowerShell):

     ```powershell
     python3.12 -m venv venv
     venv\Scripts\Activate.ps1
     ```

3. **依存関係のインストール**

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. **アプリケーションの実行**

   ```bash
   python -m src.main
   ```

   初回起動時は`src/config.json`の読み込みを試みます。キャリブレーションデータが欠落または無効な場合は、UIのキャリブレーションボタンを使用してください。

## キャリブレーションワークフロー

1. **頭部姿勢キャリブレーション**
   - 画面に向かって快適に座ります。
   - **Calibrate Head Pose**をクリックします。
   - プログレスバーが100%に達するまで静止します。ベースライン角度は自動的に保存されます。

2. **視線キャリブレーション**
   - **Calibrate Gaze**をクリックします。
   - 画面上の指示に従います（中央、左、右、上、下）。
   - 各ステップで複数のサンプルを収集します。完了後、視線しきい値が自動的に更新されます。

キャリブレーションデータと設定は`src/config.json`に保存されます。照明条件の変化や機器の移動があった場合は、いつでもキャリブレーションを再実行できます。

## コントロールと設定

- **Camera index**: ウェブカメラデバイスの選択（デフォルトは0）。
- **Smoothing window**: 頭部姿勢と視線値の移動平均ウィンドウサイズ。
- **Warning delay**: オーバーレイが表示されるまでの範囲外連続フレーム数。
- **Overlay toggle**: 常に最前面に表示される警告ウィンドウの有効/無効。
- **Head pose thresholds**: ヨー、ピッチ、ロールのキャリブレーションベースラインからの許容偏差（度）。
- **Gaze thresholds**: キャリブレーション値周辺の許容水平/垂直範囲（正規化）。
- **Logging**: `src/config.json`で有効化（`"log_to_csv": true`）すると`logs/tracking_log.csv`に書き込みます。

## オーバーレイウィンドウ

オーバーレイは、頭部姿勢と視線の両方が設定された遅延時間よりも長くしきい値を超えた場合に警告メッセージを表示する、ボーダーレスで透明なウィンドウです。ユーザーが画面に注意を戻すと、オーバーレイは自動的に非表示になります。

## PyInstallerによるパッケージング

### 自動ビルド（推奨）

1. プロジェクトの仮想環境を有効化します：
   
   **Windows:**
   ```powershell
   venv\Scripts\Activate.ps1
   ```
   
   **macOS/Linux:**
   ```bash
   source venv/bin/activate
   ```

2. ビルドスクリプトを実行します：
   
   **Windows:**
   ```bash
   build_exe.bat
   ```
   
   **macOS/Linux:**
   ```bash
   chmod +x build_exe.sh
   ./build_exe.sh
   ```

3. 実行可能ファイルは`dist/EyeTracker.exe`（単一ファイル）または`dist/EyeTracker/`ディレクトリ（フォルダ）にあります。

   **現在のモード:** ワンファイル（単一実行可能ファイル）
   - 📦 `dist/EyeTracker.exe` - スタンドアロン実行可能ファイル（約400-500 MB）
   - ⚠️ 初回起動は5-10秒かかる場合があります（一時フォルダへの展開）
   - ✅ 配布が簡単 - 1つのファイルだけ！

   ワンフォルダモード（高速起動）に切り替えるには、[ONE_FILE_BUILD.md](ONE_FILE_BUILD.md)を参照してください。

### 手動ビルド

手動でビルドする場合：

1. 仮想環境を有効化します。
2. 依存関係がインストールされていることを確認します（`pip install -r requirements.txt`）。
3. 提供されているspecファイルを使用してPyInstallerを実行します：

   ```bash
   pyinstaller EyeTracker.spec
   ```

4. バンドルされたアプリケーションは`dist/EyeTracker/`ディレクトリに表示されます。

### 重要な注意事項

- **MediaPipeファイル：** specファイルは自動的にMediaPipeモデルファイル（.binarypb）を含めます。MediaPipeモジュールの`FileNotFoundError`が発生した場合は、specファイルが使用されていることを確認してください。
- **設定ファイル：** アプリケーションは、存在しない場合は初回実行時に`config.json`を作成します。
- **クロスプラットフォーム：** 同じspecファイルがWindows、macOS、Linuxで動作します。
- **アイコン：** カスタムアイコンを追加するには、`EyeTracker.spec`の`EXE()`セクションに`icon='assets/app.ico'`を追加します。

### ビルド問題のトラブルシューティング

- **インポートエラー：** 有効化された仮想環境内からPyInstallerを実行していることを確認してください。
- **MediaPipeファイルの欠落：** specファイルがこれを自動的に処理します。問題が続く場合は、venv内にMediaPipeがインストールされていることを確認してください。
- **ファイルサイズが大きい：** バンドルされたアプリにはすべての依存関係が含まれており、通常200～400 MBです。これはMediaPipeアプリケーションでは正常です。

## プロジェクト構造

```
.
├── assets/                  # オプションのアイコンや画像
├── requirements.txt
├── env_setup.sh
├── README.md
└── src/
    ├── main.py              # PySide6 GUI
    ├── gaze_head_tracker.py # MediaPipe処理とロジック
    ├── calibration.py       # キャリブレーションデータ管理
    ├── overlay.py           # 常に最前面の警告ウィンドウ
    ├── utils.py             # スムージングと数学のヘルパー
    └── config.json          # 永続的な設定とキャリブレーションデータ
```

## トラブルシューティング

- **カメラフィードが表示されない**: 正しいカメラインデックスであること、および他のアプリがウェブカメラを使用していないことを確認してください。
- **ビデオが遅い**: スムージングウィンドウを減らすか、十分なシステムリソースを確保してください。
- **誤警告**: 現在の照明条件でキャリブレーションを再実行し、設定パネルでしきい値を調整してください。
- **パッケージングエラー**: PyInstallerが仮想環境内で実行されていること、およびMediaPipeリソースファイルがデフォルトで含まれていることを確認してください（pipでインストールされている場合、PyInstallerは自動的にコピーします）。

## 貢献

貢献を歓迎します！ガイドラインについては[CONTRIBUTING.md](CONTRIBUTING.md)をご覧ください。

### 開発環境のセットアップ

1. リポジトリをクローン
2. Python 3.12の仮想環境を作成
3. 依存関係をインストール：`pip install -r requirements.txt`
4. アプリケーションを実行：`python -m src.main`

詳細なビルド手順については、[PACKAGING_GUIDE.md](PACKAGING_GUIDE.md)を参照してください。

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

### サードパーティライセンス

このプロジェクトは以下のサードパーティライブラリを使用しています：
- **MediaPipe** - Apache License 2.0
- **PySide6** - LGPLv3
- **OpenCV** - Apache License 2.0
- **NumPy** - BSD License
- **SciPy** - BSD License

完全なライセンステキストについては、各プロジェクトのドキュメントを参照してください。

## 謝辞

- 顔検出モデルを提供するGoogle MediaPipeチーム
- PySide6を提供するQt Company
- コンピュータービジョンツールを提供するOpenCVコミュニティ

## サポート

- バグは[GitHub Issues](https://github.com/YOUR_USERNAME/eye_tracker/issues)で報告してください
- 開発に関する質問は[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください
- まず既存の[ドキュメント](README.ja.md)を確認してください

## スター履歴

このプロジェクトが役に立つと思ったら、スター⭐を付けていただけると嬉しいです

