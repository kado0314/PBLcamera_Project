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
    print("⚠️ GEMINI_API_KEY が .env または環境変数に設定されていません。")

# ▼▼▼ 修正: 安定版の 'gemini-pro' に変更 ▼▼▼
MODEL_NAME = "gemini-pro"
# ▲▲▲ 修正 ▲▲▲

def generate_fashion_feedback(image_base64: str, subscores: dict, overall_score: float) -> str:
    """
    画像と採点結果を基に、Gemini でファッションフィードバックを生成する
    """
    
    print(f"🤖 Gemini API ({MODEL_NAME}) にフィードバック生成をリクエスト中...")

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        
        img_bytes = base64.b64decode(image_base64)
        img = Image.open(io.BytesIO(img_bytes))

        subscores_str = json.dumps(subscores, indent=2, ensure_ascii=False)

        # --- Gemini への指示（プロンプト） ---
        system_prompt = f"""
あなたは日本の若者文化に詳しい、プロのファッションスタイリストです。
アップロードされた写真と、以下の採点結果（ルールベースで計算）を基に、
具体的で、親切で、建設的なフィードバックを日本語で提供してください。

# 採点結果 (100点満点中)
総合点: {round(overall_score, 1)} 点

# 項目別スコア（参考値）
{subscores_str}

# あなたのタスク
以下のフォーマットを**厳守**して、フィードバックを生成してください。
（各項目は2〜3個の箇条書きで構成してください）

## 💎 良い点 (Good Points)
* (写真を見て、特に優れている点を具体的に褒めてください)
* (例：色の組み合わせ、シルエットのバランスなど)

## 💡 改善点 (Improvement Points)
* (写真を見て、さらに良くするための具体的な改善案を提案してください)
* (例：小物の使い方、アイテムの変更案など)

## 📈 総合評価 (Overall Feedback)
(総合点が {round(overall_score, 1)} 点であった理由を、採点結果と写真の両方を踏まえて簡潔に説明してください。)
"""

        # Gemini API を呼び出す (画像とテキストを同時に送信)
        response = model.generate_content([system_prompt, img])
        
        print("✅ AIフィードバック取得完了")
        return response.text

    except Exception as e:
        print(f"⚠️ Gemini API エラー: {e}")
        return f"AIによるフィードバック生成中にエラーが発生しました。\n詳細: {e}"
