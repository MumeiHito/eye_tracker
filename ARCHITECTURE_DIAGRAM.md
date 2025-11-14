# プロジェクトアーキテクチャ図 (Project Architecture Diagrams)

このドキュメントには、視線追跡アプリケーションのアーキテクチャを説明するMermaidダイアグラムが含まれています。

## システム全体アーキテクチャ

```mermaid
graph TB
    subgraph "ユーザーインターフェース層"
        MainWindow["MainWindow<br/>(メインウィンドウ)"]
        VideoWidget["VideoWidget<br/>(カメラプレビュー)"]
        SettingsPanel["設定パネル<br/>(スクロール可能)"]
        CalibrationOverlay["CalibrationOverlayWindow<br/>(キャリブレーション用全画面オーバーレイ)"]
        OverlayWindow["OverlayWindow<br/>(通知オーバーレイ)"]
    end

    subgraph "コア処理層"
        GazeHeadTracker["GazeHeadTracker<br/>(視線・頭部姿勢追跡エンジン)"]
        CalibrationManager["CalibrationManager<br/>(キャリブレーション管理)"]
    end

    subgraph "データ処理層"
        MediaPipe["MediaPipe Face Mesh<br/>(顔ランドマーク検出)"]
        OpenCV["OpenCV<br/>(画像処理・カメラ制御)"]
        MovingAverageFilter["MovingAverageFilter<br/>(移動平均フィルター)"]
    end

    subgraph "データ永続化層"
        ConfigJSON["config.json<br/>(設定・キャリブレーションデータ)"]
    end

    subgraph "外部ライブラリ"
        PySide6["PySide6<br/>(GUIフレームワーク)"]
        NumPy["NumPy<br/>(数値計算)"]
    end

    %% ユーザーインターフェース接続
    MainWindow --> VideoWidget
    MainWindow --> SettingsPanel
    MainWindow --> CalibrationOverlay
    MainWindow --> OverlayWindow

    %% コア処理接続
    MainWindow --> GazeHeadTracker
    GazeHeadTracker --> CalibrationManager
    GazeHeadTracker --> MediaPipe
    GazeHeadTracker --> OpenCV
    GazeHeadTracker --> MovingAverageFilter

    %% データ永続化接続
    CalibrationManager --> ConfigJSON

    %% 外部ライブラリ接続
    MainWindow --> PySide6
    GazeHeadTracker --> NumPy
    OpenCV --> NumPy

    %% シグナル接続（Qt）
    GazeHeadTracker -.->|frame_ready| MainWindow
    GazeHeadTracker -.->|calibration_step| MainWindow
    GazeHeadTracker -.->|warning_state_changed| MainWindow
    GazeHeadTracker -.->|error_occurred| MainWindow

    style MainWindow fill:#e1f5ff
    style GazeHeadTracker fill:#fff4e1
    style CalibrationManager fill:#fff4e1
    style MediaPipe fill:#e8f5e9
    style ConfigJSON fill:#f3e5f5
```

## データフロー図

```mermaid
sequenceDiagram
    participant カメラ as ウェブカメラ
    participant OpenCV as OpenCV<br/>VideoCapture
    participant Tracker as GazeHeadTracker
    participant MediaPipe as MediaPipe<br/>Face Mesh
    participant Calibration as CalibrationManager
    participant Filter as MovingAverageFilter
    participant GUI as MainWindow
    participant Overlay as OverlayWindow

    カメラ->>OpenCV: フレーム取得
    OpenCV->>Tracker: フレーム読み込み
    
    loop リアルタイム処理ループ
        Tracker->>MediaPipe: 顔ランドマーク検出
        MediaPipe-->>Tracker: 468個のランドマーク
        
        Tracker->>Tracker: 頭部姿勢推定<br/>(solvePnP)
        Tracker->>Tracker: 視線ベクトル計算<br/>(虹彩位置検出)
        
        Tracker->>Filter: 角度・ベクトル平滑化
        Filter-->>Tracker: フィルター済み値
        
        Tracker->>Calibration: 閾値チェック
        Calibration-->>Tracker: 注意状態判定
        
        Tracker->>GUI: frame_readyシグナル<br/>(フレーム + データ)
        GUI->>VideoWidget: プレビュー更新<br/>(オーバーレイ描画)
        
        alt 注意が外れた場合
            Tracker->>GUI: warning_state_changed
            GUI->>Overlay: 警告メッセージ表示
        end
    end
```

## キャリブレーションプロセス

```mermaid
stateDiagram-v2
    [*] --> 待機中: アプリ起動
    
    待機中 --> 頭部姿勢キャリブレーション: ユーザーが開始
    頭部姿勢キャリブレーション --> サンプル収集: 60フレーム収集
    サンプル収集 --> ベースライン計算: 平均値計算
    ベースライン計算 --> 閾値設定: デフォルト値設定
    閾値設定 --> 保存: config.jsonに保存
    保存 --> 待機中: 完了
    
    待機中 --> 視線キャリブレーション: ユーザーが開始
    視線キャリブレーション --> 中心点: 画面中央を注視
    中心点 --> 左上: 左上角を注視
    左上 --> 右上: 右上角を注視
    右上 --> 左下: 左下角を注視
    左下 --> 右下: 右下角を注視
    右下 --> 範囲計算: 各点で45サンプル収集
    範囲計算 --> 閾値範囲設定: 水平・垂直範囲計算
    閾値範囲設定 --> 保存: config.jsonに保存
    保存 --> 待機中: 完了
    
    待機中 --> 追跡中: キャリブレーション完了後
    追跡中 --> 警告表示: 閾値超過
    警告表示 --> 追跡中: 閾値内に戻る
```

## 視線追跡アルゴリズム

```mermaid
flowchart TD
    Start([フレーム取得]) --> MediaPipe[MediaPipeで顔検出]
    MediaPipe --> Landmarks{ランドマーク<br/>検出成功?}
    
    Landmarks -->|No| End([処理スキップ])
    Landmarks -->|Yes| Extract[468個のランドマーク抽出]
    
    Extract --> HeadPose[頭部姿勢推定]
    HeadPose --> Model3D[3Dモデルポイント]
    Model3D --> SolvePnP[solvePnPで回転ベクトル計算]
    SolvePnP --> Euler[オイラー角変換<br/>Yaw, Pitch, Roll]
    
    Extract --> Iris[虹彩位置検出]
    Iris --> LeftIris[左目虹彩中心]
    Iris --> RightIris[右目虹彩中心]
    
    LeftIris --> EyeROI[目の領域計算]
    RightIris --> EyeROI
    EyeROI --> GazeVector[視線ベクトル計算<br/>正規化]
    
    Euler --> SmoothHead[移動平均フィルター<br/>頭部姿勢]
    GazeVector --> SmoothGaze[移動平均フィルター<br/>視線]
    
    SmoothHead --> CalibrationCheck[キャリブレーション<br/>閾値チェック]
    SmoothGaze --> CalibrationCheck
    
    CalibrationCheck --> Within{閾値内?}
    Within -->|Yes| AttentionOK[注意状態: OK]
    Within -->|No| AttentionLost[注意状態: 失われた]
    
    AttentionOK --> UpdateGUI[GUI更新]
    AttentionLost --> ShowWarning[警告オーバーレイ表示]
    ShowWarning --> UpdateGUI
    
    UpdateGUI --> End
```

## モジュール依存関係

```mermaid
graph LR
    subgraph "src/"
        main["main.py<br/>エントリーポイント"]
        tracker["gaze_head_tracker.py<br/>追跡エンジン"]
        calibration["calibration.py<br/>キャリブレーション管理"]
        overlay["overlay.py<br/>オーバーレイウィンドウ"]
        utils["utils.py<br/>ユーティリティ関数"]
    end

    main --> tracker
    main --> calibration
    main --> overlay
    tracker --> calibration
    tracker --> utils
    calibration --> utils
    overlay --> utils

    style main fill:#ffcccc
    style tracker fill:#ccffcc
    style calibration fill:#ccccff
    style overlay fill:#ffffcc
    style utils fill:#ffccff
```

## 設定とデータ構造

```mermaid
classDiagram
    class Settings {
        +int camera_index
        +int frame_width
        +int frame_height
        +float head_yaw_threshold
        +float head_pitch_threshold
        +float head_roll_threshold
        +float gaze_horizontal_range
        +float gaze_vertical_range
        +int smoothing_window
        +bool overlay_enabled
        +int overlay_width
        +int overlay_height
        +float overlay_pos_x
        +float overlay_pos_y
    }

    class HeadPoseCalibration {
        +Tuple baseline
        +Tuple thresholds
        +bool within_threshold()
    }

    class GazeCalibration {
        +Tuple horizontal_range
        +Tuple vertical_range
        +bool within_threshold()
    }

    class CalibrationData {
        +HeadPoseCalibration head_pose
        +GazeCalibration gaze
        +bool is_complete()
    }

    class CalibrationManager {
        -Path config_path
        +Settings settings
        +CalibrationData calibration
        +load_config()
        +save_config()
        +update_settings()
        +update_calibration()
    }

    class TrackingResult {
        +ndarray frame
        +List landmarks
        +Tuple head_angles
        +Tuple gaze_vector
        +Tuple iris_positions
        +bool head_pose_within
        +bool gaze_within
        +bool attention_ok
    }

    CalibrationManager --> Settings
    CalibrationManager --> CalibrationData
    CalibrationData --> HeadPoseCalibration
    CalibrationData --> GazeCalibration
    GazeHeadTracker --> TrackingResult
    GazeHeadTracker --> CalibrationManager
```

## GUIコンポーネント階層

```mermaid
graph TD
    MainWindow[MainWindow<br/>メインウィンドウ] --> Layout[QVBoxLayout]
    
    Layout --> TopLayout[QHBoxLayout]
    TopLayout --> VideoWidget[VideoWidget<br/>640x480固定サイズ]
    TopLayout --> ScrollArea[QScrollArea<br/>スクロール可能]
    
    ScrollArea --> SettingsPanel[設定パネル]
    SettingsPanel --> CameraSettings[カメラ設定]
    SettingsPanel --> HeadPoseSettings[頭部姿勢設定]
    SettingsPanel --> GazeSettings[視線設定]
    SettingsPanel --> OverlaySettings[オーバーレイ設定]
    SettingsPanel --> CalibrationButtons[キャリブレーションボタン]
    
    MainWindow --> OverlayWindow[OverlayWindow<br/>常に最前面]
    MainWindow --> CalibrationOverlay[CalibrationOverlayWindow<br/>全画面キャリブレーション]
    
    style MainWindow fill:#e1f5ff
    style VideoWidget fill:#fff4e1
    style SettingsPanel fill:#e8f5e9
    style OverlayWindow fill:#fce4ec
    style CalibrationOverlay fill:#f3e5f5
```

## エラーハンドリングフロー

```mermaid
flowchart TD
    Start([カメラアクセス試行]) --> Check{カメラ<br/>オープン成功?}
    
    Check -->|No| ErrorShown{エラー<br/>表示済み?}
    ErrorShown -->|No| ShowDialog[エラーダイアログ表示<br/>Retry/Cancel]
    ErrorShown -->|Yes| Wait[1秒待機]
    
    ShowDialog --> UserChoice{ユーザー選択}
    UserChoice -->|Retry| RetryFlag[リトライフラグ設定]
    UserChoice -->|Cancel| Continue[処理継続<br/>エラー表示なし]
    
    RetryFlag --> Check
    Wait --> Check
    Continue --> End([処理継続])
    
    Check -->|Yes| ResetFlags[エラーフラグリセット]
    ResetFlags --> ReadFrame[フレーム読み込み]
    
    ReadFrame --> FrameOK{フレーム<br/>読み込み成功?}
    FrameOK -->|No| ErrorCount[エラーカウンター増加]
    ErrorCount --> CountCheck{3回連続<br/>失敗?}
    CountCheck -->|Yes| ShowFrameError[フレームエラー表示]
    CountCheck -->|No| Wait
    ShowFrameError --> Wait
    
    FrameOK -->|Yes| ResetCounter[カウンターリセット]
    ResetCounter --> Process[正常処理]
    Process --> End
```

## ビルドとパッケージング

```mermaid
graph TB
    Source[ソースコード] --> PyInstaller[PyInstaller]
    PyInstaller --> SpecFile[EyeTracker.spec]
    
    SpecFile --> Hook[hook-mediapipe.py<br/>カスタムフック]
    SpecFile --> Collect[データファイル収集]
    
    Collect --> MediaPipeFiles[MediaPipeモデルファイル<br/>.binarypb, .tflite]
    Collect --> AppFiles[アプリケーションファイル<br/>.py, config.json]
    
    PyInstaller --> Build[ビルドプロセス]
    Build --> OneFile[One-Fileモード]
    OneFile --> EXE[EyeTracker.exe<br/>単一実行可能ファイル]
    
    EXE --> Runtime[実行時]
    Runtime --> TempExtract[一時フォルダに展開<br/>%TEMP%\_MEIxxxxxx]
    TempExtract --> Execute[実行]
    
    style Source fill:#e1f5ff
    style PyInstaller fill:#fff4e1
    style EXE fill:#e8f5e9
    style Runtime fill:#fce4ec
```

---

## 用語集

- **ランドマーク (Landmarks)**: 顔の特徴点（468個）
- **頭部姿勢 (Head Pose)**: 頭の向き（Yaw: 左右, Pitch: 上下, Roll: 傾き）
- **視線ベクトル (Gaze Vector)**: 視線の方向（水平・垂直）
- **虹彩 (Iris)**: 目の瞳孔周辺の色のついた部分
- **キャリブレーション (Calibration)**: 個人差に合わせた調整
- **閾値 (Threshold)**: 判定の境界値
- **移動平均フィルター (Moving Average Filter)**: 値の平滑化
- **オーバーレイ (Overlay)**: 他のウィンドウの上に表示される透明ウィンドウ

