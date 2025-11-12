import os
import base64
from flask import Flask, render_template, request
from dotenv import load_dotenv

# --- .env ファイルの読み込み ---
load_dotenv()

# --- 他の .py ファイルからロジックをインポート ---
from scorer_main import FashionScorer
from chart_generator import generate_radar_chart
from matplotlib import font_manager
import matplotlib
matplotlib.use('Agg') # ★ デプロイ環境でGUIバックエンドがないため必須

# --- Flask アプリケーションの初期化 ---
app = Flask(__name__)

# --- 【重要】フォントの事前登録 ---
def register_fonts():
    font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'KleeOne-Regular.ttf')
    font_path = os.path.abspath(font_path)
    
    if not os.path.exists(font_path):
        print(f"⚠️ Kleeフォントが見つかりません: {font_path}")
        return

    try:
        font_manager.fontManager.addfont(font_path)
        font_name = font_manager.FontProperties(fname=font_path).get_name()
        matplotlib.pyplot.rcParams["font.family"] = font_name
        print(f"✅ Kleeフォントを登録・設定しました: {font_name}")
    except Exception as e:
        print(f"⚠️ フォント設定エラー: {e}")

register_fonts() # アプリ起動時にフォントを登録

# --- ルーティング ---
GENDER_MAP = {"neutral": "指定なし", "male": "男性", "female": "女性"}
SCENE_MAP = {"date": "デート", "work": "仕事"}

@app.route("/", methods=["GET"])
def index():
    """採点ページを表示 (GET)"""
    return render_template(
        "saiten.html",
        selected_gender="neutral",
        selected_scene="date"
    )

@app.route("/saiten", methods=["POST"])
def saiten():
    """採点実行 (POST)"""
    image_file = request.files.get("image_file")
    user_gender = request.form.get("user_gender", "neutral")
    intended_scene = request.form.get("intended_scene", "date")

    if not image_file:
        return render_template(
            "saiten.html", 
            score=None, 
            feedback=["画像がアップロードされていません。"],
            selected_gender=user_gender,
            selected_scene=intended_scene
        )

    image_data_bytes = image_file.read()
    image_data_b64 = base64.b64encode(image_data_bytes).decode("utf-8")
    
    scorer = FashionScorer(user_gender=user_gender)
    result = scorer.analyze(
        image_data_b64, 
        {"intended_scene": intended_scene, "user_gender": user_gender}
    )

    aspect_scores = result.get("subscores", {})
    radar_chart_data = generate_radar_chart(aspect_scores)

    return render_template(
        "saiten.html",
        uploaded_image_data=f"data:image/png;base64,{image_data_b64}",
        score=result.get("overall_score", "N/A"),
        ai_feedback=result.get("ai_feedback", "フィードバックはありません。"), 
        radar_chart_data=radar_chart_data,
        selected_gender=user_gender,
        selected_scene=intended_scene,
        selected_gender_jp=GENDER_MAP.get(user_gender),
        selected_scene_jp=SCENE_MAP.get(intended_scene)
    )

# --- アプリケーションの実行 (ローカル実行用) ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
