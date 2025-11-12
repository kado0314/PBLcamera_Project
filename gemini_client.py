import os
import io
import json
import base64
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

load_dotenv()

try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise KeyError()
    genai.configure(api_key=api_key)
except KeyError:
    print("⚠️ GEMINI_API_KEY が .env に設定されていません。")
    # デプロイ環境では .env がないので、このエラーは出てもOK (環境変数で設定するため)

MODEL_NAME = "gemini-1.5-flash-latest"

def generate_fashion_feedback(image_base664: str, subscores: dict, overall_score: float) -> str:
    print(f"🤖 Gemini API ({MODEL_NAME}) にフィードバック生成をリクエスト中...")
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        img_bytes = base64.b64decode(image_base664)
        img = Image.open(io.BytesIO(img_bytes))
        subscores_str = json.dumps(subscores, indent=2, ensure_ascii=False)
        system_prompt = f"""
あなたは日本の若者文化に詳しい、プロのファッションスタイリストです。
... (前の手順と同じプロンプト) ...
"""
        response = model.generate_content([system_prompt, img])
        print("✅ AIフィードバック取得完了")
        return response.text
    except Exception as e:
        print(f"⚠️ Gemini API エラー: {e}")
        return f"AIによるフィードバック生成中にエラーが発生しました。\n詳細: {e}"
