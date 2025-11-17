import os
import json
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from gemini_analyzer import analyze_outfit
from visualizer import create_radar_chart, SCORE_CATEGORIES_DEFINITION

app = Flask(__name__)
app.secret_key = "your_secret_key"

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """ index.html を表示 """
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    """ 画像アップロード → AI分析 → 結果表示 """

    try:
        # ① フォームの name="image" と一致
        file = request.files.get('image')

        if file is None:
            raise ValueError("画像ファイルが送信されていません。")

        if file.filename == "":
            raise ValueError("画像ファイルが選択されていません。")

        if not allowed_file(file.filename):
            raise ValueError("アップロード可能な形式は png / jpg / jpeg / gif です。")

        # 保存（必要なら）
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        # 画像バイトデータを読み直し
        with open(save_path, "rb") as f:
            image_bytes = f.read()

        # ② Gemini に渡す
        json_string = analyze_outfit(image_bytes)

        # ③ JSON をパース
        analysis_data = json.loads(json_string)
        scores = analysis_data.get('scores')
        feedback = analysis_data.get('feedback')

        if not scores or not feedback:
            raise ValueError("AIの応答に必要なキー（scores, feedback）が不足しています。")

        # ④ レーダーチャート生成（Base64）
        chart_base64 = create_radar_chart(scores, SCORE_CATEGORIES_DEFINITION)

        # ⑤ result.html へ
        return render_template(
            'result.html',
            feedback_reason=feedback.get('reason', ''),
            feedback_improvement=feedback.get('improvement', ''),
            chart_data=chart_base64
        )

    except Exception as e:
        # error.html の表示
        return render_template('error.html', error=str(e))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
