import os
import base64
from flask import Flask, render_template, request
from dotenv import load_dotenv

# --- .env ファイルの読み込み ---
load_dotenv()

# --- 他の .py ファイルからロジックをインポート ---
from rules_db import SCORE_WEIGHTS
from feature_extractor import preprocess_image, extract_color_features, extract_silhouette_features
from chart_generator import generate_radar_chart
from scorer_main import FashionScorer

from matplotlib import font_manager
import matplotlib
matplotlib.use('Agg') # デプロイ環境で必須

# --- Flask アプリケーションの初期化 ---
app = Flask(__name__)

# --- フォントの事前登録 ---
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

# --- ルーティング ---
# ▼▼▼ 修正 ▼▼▼
# GENDER_MAP を削除
SCENE_MAP = {"date": "デート", "work": "仕事"}
# ▲▲▲ 修正 ▲▲▲

@app.route("/", methods=["GET"])
def index():
    """採点ページを表示 (GET)"""
    # ▼▼▼ 修正: selected_gender を削除 ▼▼▼
    return render_template(
        "saiten.html",
        selected_scene="date",
        score=None
    )
    # ▲▲▲ 修正 ▲▲▲

@app.route("/saiten", methods=["POST"])
def saiten():
    """採点実行 (POST)"""
    image_file = request.files.get("image_file")
    
    # ▼▼▼ 修正 ▼▼▼
    # フォームからTPOのみ取得
    intended_scene = request.form.get("intended_scene", "date")
    # 性別は "neutral" で固定
    user_gender = "neutral" 
    # ▲▲▲ 修正 ▲▲▲

    if not image_file:
        # 画像がない場合
        return render_template(
            "saiten.html", 
            score=None, 
            ai_feedback="画像がアップロードされていません。",
            # ▼▼▼ 修正: selected_gender を削除 ▼▼▼
            selected_scene=intended_scene
            # ▲▲▲ 修正 ▲▲▲
        )

    image_data_bytes = image_file.read()
    image_data_b64 = base64.b64encode(image_data_bytes).decode("utf-8")
    
    # ▼▼▼ 修正: user_gender は固定値の "neutral" を使用 ▼▼▼
    scorer = FashionScorer(user_gender=user_gender)
    metadata = {
        "intended_scene": intended_scene, 
        "user_gender": user_gender # "neutral" が渡される
    }
    # ▲▲▲ 修正 ▲▲▲
    
    result = scorer.analyze(image_data_b64, metadata)

    aspect_scores = result.get("subscores", {})
    radar_chart_data = generate_radar_chart(aspect_scores)

    return render_template(
        "saiten.html",
        uploaded_image_data=f"data:image/png;base64,{image_data_b64}",
        score=result.get("overall_score", "N/A"),
        ai_feedback=result.get("ai_feedback", "フィードバックはありません。"),
        radar_chart_data=radar_chart_data,
        # ▼▼▼ 修正: selected_gender を削除 ▼▼▼
        selected_scene=intended_scene,
        selected_scene_jp=SCENE_MAP.get(intended_scene)
        # ▲▲▲ 修正 ▲▲▲
    )

# --- アプリケーションの実行 ---
if __name__ == "__main__":
    register_fonts()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
