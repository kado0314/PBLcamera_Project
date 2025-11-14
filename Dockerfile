# ベースイメージとしてPython 3.10の軽量版を選択
FROM python:3.10-slim-buster

# --- OSレベルの依存関係（日本語フォント）をインストール ---
# これがmatplotlibの日本語文字化けを解決する鍵です [11, 13, 14]
RUN apt-get update && apt-get install -y \
    fonts-ipafont-gothic \  # 日本語フォント (IPAフォント)
    fontconfig \            # フォントキャッシュを管理するツール
    --no-install-recommends \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && fc-cache -fv # フォントキャッシュを再構築

# Pythonのログがバッファリングされず、Renderのログに即時表示されるように設定
ENV PYTHONUNBUFFERED=1

# コンテナ内の作業ディレクトリ
WORKDIR /app

# 最初にrequirements.txtだけをコピーし、パッケージをインストール
# (これにより、コード変更時もパッケージの再インストールをスキップでき高速化します)
COPY requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt [20, 21, 22]

# アプリケーションの全コードをコピー
COPY..

# Renderがコンテナに接続するために使用するポート
ENV PORT 10000

# アプリケーションの起動コマンド (Gunicornを使用 [22, 23, 24])
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
