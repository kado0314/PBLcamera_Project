import os
import base64
from flask import Flask, render_template, request
from dotenv import load_dotenv

# --- .env ファイルの読み込み ---
load_dotenv()

# --- 他の .py ファイルからロジックをインポート ---
# (循環参照を避けるため、インポートの順番が重要です)
from rules_db import SCORE_WEIGHTS # 依存関係のないものを先に
from feature_extractor import preprocess_image, extract_color_features, extract_silhouette_features
from chart_generator import generate_radar_chart
from scorer_main import FashionScorer

from matplotlib import font_manager
import matplotlib
# ★ デプロイ環境（GUIがないサーバー）で Matplotlib を動かすための必須設定
matplotlib.use('Agg') 

# --- Flask アプリケーションの初期化 ---
app = Flask(__name__)

# --- 【重要】フォントの事前登録 ---
# アプリ起動時に一度だけ実行
def register_fonts():
    # 'fonts' フォルダが app.py と同じ階層にあると仮定
    font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'KleeOne-Regular.ttf')
    font_path = os.path.abspath(font_path)
    
    if not os.path.exists(font_path):
        print(f"⚠️ Kleeフォントが見つかりません: {font_path}")
        print("⚠️ デフォルトフォントを使用します。")
        return

    try:
        font_manager.fontManager.addfont(font_path)
        # Matplotlib の rcParams にも設定
        font_name = font_manager.FontProperties(fname=font_path).get_name()
        matplotlib.pyplot.rcParams["font.family"] = font_name
        print(f"✅ Kleeフォントを登録・設定しました: {font_name}")
    except Exception as e:
        print(f"⚠️ フォント設定エラー: {e}")

# --- ルーティング (routes.py の役割) ---
GENDER_MAP = {"neutral": "指定なし", "male": "男性", "female": "女性"}
SCENE_MAP = {"date": "デート", "work": "仕事"}

@app.route("/", methods=["GET"])
def index():
    """採点ページを表示 (GET)"""
    # 初期表示時のデフォルト値を指定
    return render_template(
        "saiten.html",
        selected_gender="neutral",
        selected_scene="date",
        score=None
    )

@app.route("/saiten", methods=["POST"])
def saiten():
    """採点実行 (POST)"""
    image_file = request.files.get("image_file")
    
    # フォームからデータを取得。値がない場合はデフォルト値を設定
    user_gender = request.form.get("user_gender", "neutral")
    intended_scene = request.form.get("intended_scene", "date")

    if not image_file:
        # 画像がない場合でも、フォームの選択状態を維持してページを再表示
        return render_template(
            "saiten.html", 
            score=None, 
            ai_feedback="画像がアップロードされていません。", # feedback の代わりに ai_feedback を使う
            selected_gender=user_gender,
            selected_scene=intended_scene
        )

    # 画像をBase64化 (Geminiとフロントエンドで共用)
    image_data_bytes = image_file.read()
    image_data_b64 = base64.b64encode(image_data_bytes).decode("utf-8")
    
    # FashionScorerにフォームの値を渡す
    scorer = FashionScorer(user_gender=user_gender)
    metadata = {
        "intended_scene": intended_scene, 
        "user_gender": user_gender
    }
    result = scorer.analyze(image_data_b64, metadata)

    # グラフ生成
    aspect_scores = result.get("subscores", {}) # デフォルトを空の辞書に
    radar_chart_data = generate_radar_chart(aspect_scores)

    # テンプレートにすべての結果を渡す
    return render_template(
        "saiten.html",
        uploaded_image_data=f"data:image/png;base64,{image_data_b64}", # アップロード画像表示用
        score=result.get("overall_score", "N/A"),
        ai_feedback=result.get("ai_feedback", "フィードバックはありません。"), # ★ AIのフィードバック
        radar_chart_data=radar_chart_data,
        selected_gender=user_gender,
        selected_scene=intended_scene,
        selected_gender_jp=GENDER_MAP.get(user_gender),
        selected_scene_jp=SCENE_MAP.get(intended_scene)
    )

# --- アプリケーションの実行 ---
if __name__ == "__main__":
    register_fonts() # 起動時にフォントを登録
    port = int(os.environ.get("PORT", 5000))
    # debug=True はローカルでの実行時のみ。
    # gunicorn が実行するときは debug=False になります。
    app.run(debug=True, host="0.0.0.0", port=port)
