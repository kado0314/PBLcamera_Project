import os
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import io
from PIL import Image

# --- Gemini API 初期化 ---
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("環境変数 GEMINI_API_KEY が設定されていません。")

genai.configure(api_key=api_key)


def get_system_prompt() -> str:
    """AI が必ず JSON を返すようにするプロンプト"""
    return """
    あなたは高名なファッション評論家です。
    提示された画像のファッションコーディネートを、性別には一切言及せず、中立的な立場で分析してください。

    必ず RFC 8259 準拠の JSON オブジェクトのみで回答してください。

    JSON のトップには `scores` と `feedback` の2つのキーを持ちます。

    【scores】
    - color_harmony: 0〜20
    - fit_and_silhouette: 0〜20
    - item_coordination: 0〜15
    - cleanliness_material: 0〜15
    - accessories_balance: 0〜10
    - trendness: 0〜10
    - tpo_suitability: 0〜5
    - photogenic_quality: 0〜5

    【feedback】
    - reason: スコアの根拠
    - improvement: 改善案
    """


def analyze_outfit(image_bytes: bytes) -> str:
    """画像を Gemini に渡して JSON の分析結果を返す"""

    # PIL で画像チェック
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception:
        raise ValueError("無効な画像ファイルがアップロードされました。")

    # --- 画像を Gemini 用フォーマットに変換 ---
    # MIME の特定
    format = img.format.lower() if img.format else "jpeg"
    mime_type = f"image/{format}"

    # バイト化
    img_bytes = io.BytesIO()
    img.save(img_bytes, format=img.format)
    img_bytes = img_bytes.getvalue()

    image_part = {
        "mime_type": mime_type,
        "data": img_bytes
    }

    # --- JSON 出力を強制 ---
    json_cfg = GenerationConfig(
        response_mime_type="application/json"
    )

    # --- 最新モデル（ここが重要）---
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=json_cfg
    )

    prompt = [get_system_prompt(), image_part]

    # --- API 呼び出し ---
    try:
        response = model.generate_content(prompt)
        return response.text   # JSON 文字列
    except Exception as e:
        raise ValueError(f"Gemini APIの呼び出しに失敗しました: {e}")
