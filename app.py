import os
from flask import Flask, request, redirect, url_for, render_template, flash, send_from_directory
from werkzeug.utils import secure_filename

# --- 1. 設定: 環境の基盤 ---

# アップロードされたファイルを保存するディレクトリ
# Renderでは、永続ディスク（有料）または一時的なファイルシステムを使用します。
# この例では、スクリプトと同じ階層にある 'uploads' フォルダを想定します。
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')

# アップロードを許可する拡張子のセット
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)

# Flaskアプリケーションの設定
app.config = UPLOAD_FOLDER
# 'flash' メッセージ機能のためにシークレットキーが必要です
app.config = os.urandom(24) 
# アップロードサイズの制限（例：16MB）
app.config = 16 * 1024 * 1024 

# 拡張子が許可されているかチェックするヘルパー関数
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1).lower() in ALLOWED_EXTENSIONS

# --- 2. ルーティング：中核機能 ---

@app.route('/', methods=)
def upload_file():
    """
    ファイルアップロードを処理し、フォームを表示するメインルート。
    GETリクエスト：アップロードフォームを返します。
    POSTリクエスト：ファイルを検証し、保存します。
    """
    
    # --- 3. POSTロジック (ファイル受信) ---
    if request.method == 'POST':
        # 3a. リクエストの検証
        if 'file' not in request.files:
            flash('リクエストにファイルパートが含まれていません')
            return redirect(request.url)
        
        file = request.files['file']

        # 3b. ファイル未選択のハンドリング
        # ユーザーがファイルを選択せずにフォームを送信した場合、
        # ブラウザはファイル名が空のファイルを送信します。
        if file.filename == '':
            flash('ファイルが選択されていません')
            return redirect(request.url)

        # 3c. ファイルの検証と保存
        if file and allowed_file(file.filename):
            
            # ---!!! セキュリティ最重要ポイント!!! ---
            # 
            # 脆弱なコード (非推奨): f.save(f.filename) 
            #   これは「パス・トラバーサル（Path Traversal）」脆弱性を含みます。
            #   悪意のあるユーザーが '../../app.py' のようなファイル名を送信すると、
            #   サーバー上の重要なファイルを上書きされる可能性があります。
            #
            # 安全なコード (必須):
            #   werkzeug.utils.secure_filename() を使用します。
            #   これは、'../' や '/' のような危険なシーケンスをファイル名から
            #   安全に除去します (例: '../../app.py' -> 'app.py')。
            #
            filename = secure_filename(file.filename)
            
            # フォルダが存在しない場合に作成する
            if not os.path.exists(app.config):
                os.makedirs(app.config)
                
            save_path = os.path.join(app.config, filename)
            file.save(save_path)
            
            flash('ファイルが正常にアップロードされました')
            # アップロードされたファイルを表示するルートにリダイレクト
            return redirect(url_for('download_file', name=filename))
        
        else:
            flash('許可されていないファイルタイプです')
            return redirect(request.url)

    # --- 4. GETロジック (フォーム表示) ---
    # GETリクエスト、またはPOST処理が失敗した場合は、
    # 'index.html' テンプレートをレンダリングします。
    return render_template('index.html')


@app.route('/uploads/<name>')
def download_file(name):
    """
    アップロードされたファイルを提供（サーブ）するためのルート。
    send_from_directory は、指定されたディレクトリ外のファイルへの
    アクセス（パス・トラバーサル）を防ぐため、安全です。
    """
    return send_from_directory(app.config, name)

if __name__ == '__main__':
    app.run(debug=True)
