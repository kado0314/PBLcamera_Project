from datetime import datetime
import json
from typing import Dict, List, Any
import numpy as np
import cv2
import base64

from rules_db import SCORE_WEIGHTS, BIAS_ADJUSTMENTS, TPO_RULES
from feature_extractor import (
    preprocess_image, 
    extract_color_features, 
    extract_silhouette_features
)
from gemini_client import generate_fashion_feedback

class FashionScorer:
    MODEL_VERSION = "v1.2.0"
    def __init__(self, user_gender: str = "neutral", user_locale: str = "ja-JP"):
        self.user_gender = user_gender
        self.user_locale = user_locale
    
    def load_image_from_base64(self, image_base64: str) -> np.ndarray or None:
        # (前の手順と同じコード)
        try:
            img_bytes = base64.b64decode(image_base64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            return None

    def _score_color_harmony(self, color_features: Dict[str, Any]) -> float:
        # (前の手順と同じコード)
        score = 0.0
        max_colors = 4
        primary_colors_count = color_features["primary_colors_count"]
        if primary_colors_count <= max_colors:
            score += 10 * (1 - (primary_colors_count / max_colors * 0.5))
        else:
            score += 3
        avg_saturation = color_features["avg_saturation_ratio"]
        if 0.2 < avg_saturation < 0.6:
            score += 10
        elif avg_saturation <= 0.2:
            score += 5
        else:
            score += 3
        return round(min(score, SCORE_WEIGHTS["color_harmony"]), 1)

    def _score_fit_and_silhouette(self, silhouette_features: Dict[str, Any]) -> float:
        # (前の手順と同じコード)
        score = 0.0
        max_score = SCORE_WEIGHTS["fit_and_silhouette"]
        if silhouette_features.get("is_oversized"):
            score = max(0, max_score - 10.0)
        else:
            score += 15.0
        if silhouette_features.get("jacket_fit_score", 0) > 0.8:
            score += 5.0
        return round(min(score, max_score), 1)

    def _score_other_subscores(self, subscores: Dict[str, float]) -> Dict[str, float]:
        # (前の手順と同じコード)
        remaining_scores = {}
        for key, max_val in SCORE_WEIGHTS.items():
            if key not in subscores:
                remaining_scores[key] = round(max_val * np.random.uniform(0.7, 0.9), 1)
        return remaining_scores

    def analyze(self, image_base64: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        # (前の手順と同じコード)
        img = self.load_image_from_base64(image_base64)
        if img is None:
            return {"error": "Invalid image data."}
        preprocessed_img = preprocess_image(img)
        user_gender = metadata.get("user_gender", "neutral")
        color_features = extract_color_features(preprocessed_img)
        silhouette_features = extract_silhouette_features(preprocessed_img, user_gender)
        
        subscores: Dict[str, float] = {}
        score_c = self._score_color_harmony(color_features)
        subscores["color_harmony"] = score_c
        score_f = self._score_fit_and_silhouette(silhouette_features)
        subscores["fit_and_silhouette"] = score_f
        subscores.update(self._score_other_subscores(subscores))
        overall_score = sum(subscores.values())

        # Gemini API でフィードバックを生成
        ai_feedback = generate_fashion_feedback(image_base64, subscores, overall_score)

        output = {
            "overall_score": round(overall_score, 1),
            "subscores": subscores,
            "ai_feedback": ai_feedback,
            "warnings": [],
            "metadata": { ... },
            "ui_messages": [ ... ]
        }
        return output
