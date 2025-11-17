FROM python:3.9-slim

WORKDIR /app

# 日本語フォント & fontconfigをインストール
RUN apt-get update \
    && apt-get install -y \
       fonts-ipafont-gothic \
       fontconfig \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# フォントキャッシュ更新
RUN fc-cache -f -v

# Python依存パッケージ
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコピー
COPY . .

EXPOSE 5000

# 本番では gunicorn を推奨
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
