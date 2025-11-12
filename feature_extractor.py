# feature_extractor.py (修正版)
import cv2
import numpy as np
from typing import Dict, Any
from .rules_db import BIAS_ADJUSTMENTS

# MediaPipe は重いので「遅延初期化」。最初は None にしておく。
pose_estimator = None
mp = None

def _ensure_pose_estimator():
    global pose_estimator, mp
    if pose_estimator is None:
        try:
            import mediapipe as _mp
            mp = _mp
            mp_pose = mp.solutions.pose
            # model_complexity=0 で軽量化、static_image_mode=True にして単発処理向け
            pose_estimator = mp_pose.Pose(static_image_mode=True, model_complexity=0, enable_segmentation=False)
            print("✅ MediaPipe pose_estimator initialized (light mode).")
        except Exception as e:
            pose_estimator = None
            mp = None
            print(f"⚠️ Failed to initialize MediaPipe: {e}")

def preprocess_image(img: np.ndarray, max_side: int = 400) -> np.ndarray:
    """アップスケールを避け、最大辺を max_side に合わせる（元画像が小さければ拡大しない）"""
    h, w = img.shape[:2]
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img

def extract_color_features(img: np.ndarray) -> Dict[str, Any]:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    unique_colors_count = np.unique(hsv[:,:,0]).size
    avg_saturation = np.mean(hsv[:,:,1]) / 255.0
    return {
        "hsv_hist": cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256]).flatten(),
        "primary_colors_count": min(unique_colors_count // 50, 6),
        "avg_saturation_ratio": avg_saturation
    }

def extract_silhouette_features(img: np.ndarray, user_gender: str) -> Dict[str, Any]:
    """
    MediaPipe を使って姿勢を推定。MediaPipe が初期化できない場合は軽量なダミーを返す。
    """
    # まず、必要なら初期化
    _ensure_pose_estimator()

    features = {
        "shoulder_to_height_ratio": 0.25,
        "hip_to_height_ratio": 0.3,
        "is_oversized": False,
        "detection_confidence": 0.0,
        "jacket_fit_score": 0.0
    }

    if pose_estimator is None:
        # MediaPipe が使えない環境ならデフォルトを返す（Render Free 対応）
        return features

    # MediaPipe expects RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    try:
        results = pose_estimator.process(img_rgb)
    except Exception as e:
        print(f"⚠️ pose_estimator.process failed: {e}")
        return features

    if not results.pose_landmarks:
        return features

    landmarks = results.pose_landmarks.landmark
    try:
        left_shoulder = landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
        left_ankle = landmarks[mp.solutions.pose.PoseLandmark.LEFT_ANKLE]
        right_ankle = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_ANKLE]

        if (left_shoulder.visibility < 0.5 or right_shoulder.visibility < 0.5 or
            left_ankle.visibility < 0.5 or right_ankle.visibility < 0.5):
            return features

        avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        avg_ankle_y = (left_ankle.y + right_ankle.y) / 2
        estimated_height = abs(avg_ankle_y - avg_shoulder_y)
        if estimated_height < 0.1:
            return features

        shoulder_width = abs(left_shoulder.x - right_shoulder.x)
        shoulder_ratio = shoulder_width / estimated_height
        features["shoulder_to_height_ratio"] = shoulder_ratio
        features["detection_confidence"] = float(np.mean([
            left_shoulder.visibility, right_shoulder.visibility,
            left_ankle.visibility, right_ankle.visibility
        ]))

        target_range = BIAS_ADJUSTMENTS.get(user_gender, BIAS_ADJUSTMENTS["neutral"])["silhouette_std_range"]
        features["is_oversized"] = shoulder_ratio > target_range[1]
        # jacket_fit_score を簡易算出（visibility と比率から）
        features["jacket_fit_score"] = max(0.0, min(1.0, (1.0 - abs(shoulder_ratio - sum(target_range)/2))))
    except Exception as e:
        print(f"⚠️ Error computing landmarks: {e}")

    return features
