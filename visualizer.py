import io
import base64
import matplotlib.pyplot as plt
import numpy as np

# セクション4.1で定義したスコア定義
SCORE_CATEGORIES_DEFINITION = {
    "color_harmony": ("色の調和", 20),
    "fit_and_silhouette": ("フィット感とシルエット", 20),
    "item_coordination": ("アイテムの組み合わせ", 15),
    "cleanliness_material": ("清潔感と素材", 15),
    "accessories_balance": ("小物のバランス", 10),
    "trendness": ("トレンド感", 10),
    "tpo_suitability": ("TPO適合性", 5),
    "photogenic_quality": ("写真映え", 5),
}

def create_radar_chart(scores: dict, definition: dict) -> str:
    """ AIからのスコア辞書を受け取り、Base64エンコードされたレーダーチャート画像を返す """
    
    labels =
    max_values =
    values =
    
    # 定義テーブルの順序でスコアを整理し、正規化する (4.1 罠1)
    for key, (label, max_val) in definition.items():
        labels.append(label)
        max_values.append(max_val)
        # AIのスコアを0-1.0の範囲に正規化
        normalized_value = scores.get(key, 0) / max_val
        values.append(normalized_value)

    num_vars = len(labels)
    
    # 角度を計算 
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    
    # グラフを閉じるために最初と最後のデータを接続 (4.1 罠2)
    values += values[:1]
    angles += angles[:1]
    
    # Matplotlibのフォント設定（日本語が文字化けしないように）
    # デプロイ環境に日本語フォントがない場合があるため、汎用的なフォントを指定
    # (より確実な方法は、フォントファイルをリポジトリに同梱することです)
    plt.rcParams['font.sans-serif'] =

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    
    # データをプロット 
    ax.plot(angles, values, color='blue', linewidth=2)
    ax.fill(angles, values, color='blue', alpha=0.25)
    
    # 軸（カテゴリ）ラベルの設定 (4.1 罠3) 
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    
    # 軸の範囲を 0.0 から 1.0 (正規化後の最大値) に設定
    ax.set_ylim(0, 1.0)
    
    # --- ここからインメモリ処理 [14, 55] ---
    
    # 1. メモリバッファを作成
    buf = io.BytesIO()
    
    # 2. グラフをディスクではなくバッファに保存
    fig.savefig(buf, format='png', bbox_inches='tight')
    
    # 3. メモリリークを防ぐために明示的に閉じる [15]
    plt.close(fig)
    
    # 4. バッファのバイナリデータをBase64にエンコード [13, 15]
    data = base64.b64encode(buf.getvalue())
    
    # 5. HTMLの <img src="..."> で使えるよう、ASCII文字列にデコードして返す
    return data.decode('ascii')
