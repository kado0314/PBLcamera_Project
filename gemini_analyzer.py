import os
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import io
from PIL import Image

# 環境変数からAPIキーを読み込む 
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません。")
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"APIキーの設定中にエラーが発生しました: {e}")
    # アプリケーションの起動を継続させるか、ここで停止させるかは設計によりますが、
    # キーがないと機能しないため、エラーを明示します。
    pass

def get_system_prompt() -> str:
    """ セクション2.1で設計した詳細な日本語の指示プロンプトを返す """
    return """
    あなたは高名なファッション評論家です。
    提示された画像のファッションコーディネートを、性別には一切言及せず、中立的な立場で分析してください。
    あなたの応答は、必ず RFC 8259 準拠のJSONオブジェクトのみでなければなりません。
    
    このJSONオブジェクトは、`scores` と `feedback` という2つのトップレベルキーを持ちます。
    
    1. `scores` キー: 
    以下の8項目を評価し、その結果をネストされたJSONオブジェクトとして格納してください。
    各項目の最大値（満点）は厳守してください。
    - "color_harmony": 0〜20点 (色の調和)
    - "fit_and_silhouette": 0〜20点 (フィット感とシルエット)
    - "item_coordination": 0〜15点 (アイテム同士の組み合わせ)
    - "cleanliness_material": 0〜15点 (清潔感と素材の質)
    - "accessories_balance": 0〜10点 (小物（靴、バッグ等）のバランス)
    - "trendness": 0〜10点 (トレンド感)
    - "tpo_suitability": 0〜5点 (TPOへの適合性)
    - "photogenic_quality": 0〜5点 (写真映え)
    
    2. `feedback` キー:
    以下の2つのキーを持つネストされたJSONオブジェクトを格納してください。
    - "reason": なぜそのスコアになったのかの具体的な根拠を、日本語の文字列で記述してください。
    - "improvement": このコーディネートをさらに良くするための具体的な改善アドバイスを、日本語の文字列で記述してください。
    """

def analyze_outfit(image_bytes: bytes) -> str:
    """ 画像バイトを受け取り、Gemini 1.5 Flashで分析し、JSON文字列を返す """
    
    # JSONモードを強制する設定 
    json_config = GenerationConfig(response_mime_type="application/json")
    
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config=json_config
    )
    
    # バイトデータをインメモリでPIL Imageオブジェクトに変換 [53]
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception:
        raise ValueError("無効な画像ファイルがアップロードされました。")

    # テキストプロンプトと画像オブジェクトをリストで渡す [4, 18, 54]
    prompt_parts = [
        get_system_prompt(),
        img
    ]
    
    # API呼び出し
    try:
        response = model.generate_content(prompt_parts)
        # response.text には構文的に保証されたJSON文字列が格納されている
        return response.text
    except Exception as e:
        # APIエラー（レート制限、セーフティブロックなど）を捕捉
        raise ValueError(f"Gemini APIの呼び出しに失敗しました: {e}")
