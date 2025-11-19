import os
import json
import base64
import io
from flask import Flask, render_template, request, redirect, url_for, Blueprint
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import matplotlib
# サーバーサイド(GUIなし)でグラフを描画するために必須
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')

# --- Gemini API設定 ---
GENAI_API_KEY = os.environ.get('GOOGLE_API_KEY')

if not GENAI_API_KEY:
    print("Warning: GOOGLE_API_KEY is not set.")
else:
    genai.configure(api_key=GENAI_API_KEY)

# ★ここで最新モデルを指定します
MODEL_NAME = "gemini-2.5-flash"

generation_config = {
    "temperature": 1,
    "response_mime_type": "application/json",
}

# 安全のためAPIキーがある場合のみモデル初期化
model = None
if GENAI_API_KEY:
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=generation_config,
        )
    except Exception as e:
        print(f"Model initialization error: {e}")

# Blueprint設定
scoring_bp = Blueprint('scoring', __name__)

# 採点基準定義
SCORING_CRITERIA = {
    "color_harmony": "色の調和",
    "fit_and_silhouette": "フィット感とシルエット",
    "item_coordination": "アイテムの組み合わせ",
    "cleanliness_material": "清潔感と素材",
    "accessories_balance": "小物のバランス",
    "trendness": "トレンド感",
    "tpo_suitability": "TPO適合性",
    "photogenic_quality": "写真映え"
}

def create_radar_chart(scores):
    """レーダーチャートを作成しBase64文字列で返す"""
    labels = [v for v in SCORING_CRITERIA.values()]
    # キー順に値を取得。キーが無い場合は0点とする
    values = [scores.get(k, 0) for k in SCORING_CRITERIA.keys()] 
    
    # 閉じた多角形にするためにデータを一周させる
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='skyblue', alpha=0.25)
    ax.plot(angles, values, color='blue', linewidth=2)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 20) # 各項目の満点目安に合わせて調整
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"data:image/png;base64,{data}"

@scoring_bp.route('/', methods=['GET', 'POST'])
def saiten():
    if request.method == 'GET':
        return render_template('index.html', score=None)

    if request.method == 'POST':
        if not model:
            return render_template('index.html', score=None, error="APIキー設定エラー: サーバー管理者に連絡してください。")

        file = request.files.get('image_file')
        user_gender = request.form.get('user_gender', 'neutral')
        intended_scene = request.form.get('intended_scene', 'friends')

        if not file or file.filename == '':
            return render_template('index.html', score=None, error="画像を選択してください")

        try:
            # 画像処理
            image = Image.open(file)
            
            # プレビュー表示用Base64
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            uploaded_image_data = f"data:image/png;base64,{img_b64}"

            # プロンプト作成
            prompt = f"""
            あなたはプロのファッションスタイリストです。以下の画像を分析し、採点してください。
            ユーザー属性: {user_gender}, 想定シーン: {intended_scene}
            
            以下のJSON形式のみで出力してください:
            {{
                "total_score": (0-100の整数),
                "recommendation": "(一言コメント)",
                "feedback_points": ["(良い点・改善点1)", "(良い点・改善点2)", "(良い点・改善点3)"],
                "details": {{
                    "color_harmony": (0-20), "fit_and_silhouette": (0-20),
                    "item_coordination": (0-15), "cleanliness_material": (0-15),
                    "accessories_balance": (0-10), "trendness": (0-10),
                    "tpo_suitability": (0-5), "photogenic_quality": (0-5)
                }}
            }}
            """

            # 推論実行
            response = model.generate_content([prompt, image])
            result = json.loads(response.text)
            
            # グラフ作成
            radar_chart_data = create_radar_chart(result.get('details', {}))

            return render_template(
                'index.html',
                score=result.get('total_score', 0),
                recommendation=result.get('recommendation', ''),
                feedback=result.get('feedback_points', []),
                radar_chart_data=radar_chart_data,
                uploaded_image_data=uploaded_image_data,
                selected_gender=user_gender,
                selected_scene=intended_scene
            )

        except Exception as e:
            print(f"Scoring Error: {e}")
            return render_template('index.html', score=None, error="採点中にエラーが発生しました。もう一度お試しください。")

app.register_blueprint(scoring_bp, url_prefix='/scoring')

@app.route('/')
def index():
    return redirect(url_for('scoring.saiten'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
