import os
import json
import base64
import io
from flask import Flask, render_template, request, redirect, url_for, Blueprint
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_key')

# APIキー設定
GENAI_API_KEY = os.environ.get('GOOGLE_API_KEY')

# --- 診断機能: 利用可能なモデルをログに出す ---
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)
    print("----------- MODEL CHECK START -----------")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Available: {m.name}")
    except Exception as e:
        print(f"List models failed: {e}")
    print("----------- MODEL CHECK END -----------")
    
    # モデル設定（安全策として gemini-1.5-flash を指定）
    # エラーが出る場合は、ログに出てきた "Available: models/..." の名前をコピーして使います
    MODEL_NAME = "gemini-1.5-flash" 
    
    generation_config = {
        "temperature": 1,
        "response_mime_type": "application/json",
    }
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
    )
else:
    model = None
    print("API Key not found.")

scoring_bp = Blueprint('scoring', __name__)

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
    labels = list(SCORING_CRITERIA.values())
    values = [scores.get(k, 0) for k in SCORING_CRITERIA.keys()]
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color='skyblue', alpha=0.25)
    ax.plot(angles, values, color='blue', linewidth=2)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 20)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return f"data:image/png;base64,{base64.b64encode(buf.getbuffer()).decode('ascii')}"

@scoring_bp.route('/', methods=['GET', 'POST'])
def saiten():
    if request.method == 'GET':
        return render_template('index.html', score=None)

    if request.method == 'POST':
        if not model:
            return render_template('index.html', score=None, error="APIキー設定エラー")

        file = request.files.get('image_file')
        if not file or file.filename == '':
            return render_template('index.html', score=None, error="画像なし")

        try:
            image = Image.open(file)
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            uploaded_image_data = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"

            prompt = f"""
            ファッションスタイリストとして採点してください。
            性別: {request.form.get('user_gender')}, シーン: {request.form.get('intended_scene')}
            JSON出力必須:
            {{
                "total_score": 0-100,
                "recommendation": "コメント",
                "feedback_points": ["点1", "点2", "点3"],
                "details": {{
                    "color_harmony": 0-20, "fit_and_silhouette": 0-20,
                    "item_coordination": 0-15, "cleanliness_material": 0-15,
                    "accessories_balance": 0-10, "trendness": 0-10,
                    "tpo_suitability": 0-5, "photogenic_quality": 0-5
                }}
            }}
            """

            response = model.generate_content([prompt, image])
            result = json.loads(response.text)
            
            return render_template(
                'index.html',
                score=result.get('total_score', 0),
                recommendation=result.get('recommendation', ''),
                feedback=result.get('feedback_points', []),
                radar_chart_data=create_radar_chart(result.get('details', {})),
                uploaded_image_data=uploaded_image_data,
                selected_gender=request.form.get('user_gender'),
                selected_scene=request.form.get('intended_scene')
            )

        except Exception as e:
            print(f"Scoring Error: {e}")
            # エラーを画面に出してデバッグしやすくする
            return render_template('index.html', score=None, error=f"エラー詳細: {e}")

app.register_blueprint(scoring_bp, url_prefix='/scoring')

@app.route('/')
def index():
    return redirect(url_for('scoring.saiten'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
