import os
import json
from flask import Flask, request, render_template, redirect, url_for
from gemini_analyzer import analyze_outfit
from visualizer import create_radar_chart, SCORE_CATEGORIES_DEFINITION

app = Flask(__name__)

# APIキーが設定されているか起動時に確認
if not os.environ.get("GEMINI_API_KEY"):
    print("警告: 環境変数 'GEMINI_API_KEY' が設定されていません。")

@app.route('/')
def index():
    """ index.html (アップロードフォーム) を表示 """
    return render_template('index.html')

@app.route('/upload', methods=)  # <-- ★★★ 構文エラーを修正しました
def upload():
    """ 画像アップロードとAI分析の処理 """
    
    # ファイルアップロードの検証 [1, 3]
    if 'image' not in request.files or request.files['image'].filename == '':
        # ファイルが選択されていない場合は、トップページにリダイレクト
        return redirect(url_for('index'))
    
    file = request.files['image']
    
    try:
        # ファイルをインメモリで読み込む
        image_bytes = file.read()
        
        # AIエンジンを呼び出す
        json_string = analyze_outfit(image_bytes)
        
        # AIのJSON応答をパース
        analysis_data = json.loads(json_string)
        
        scores = analysis_data.get('scores')
        feedback = analysis_data.get('feedback')

        # AIの応答スキーマ検証
        if not scores or not feedback:
            raise ValueError("AIの応答に必要なキー（scores, feedback）が含まれていません。")

        # 可視化エンジンを呼び出し、Base64文字列を取得
        chart_base64 = create_radar_chart(scores, SCORE_CATEGORIES_DEFINITION)
        
        # 全てのデータを result.html に渡して表示
        return render_template('result.html',
                                 feedback_reason=feedback.get('reason', '分析エラー'),
                                 feedback_improvement=feedback.get('improvement', 'なし'),
                                 chart_data=chart_base64)
    
    except Exception as e:
        # 汎用エラーハンドリング
        return render_template('error.html', error=str(e))

if __name__ == '__main__':
    # このブロックは 'python app.py' でローカルテストする時のみ実行される
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
