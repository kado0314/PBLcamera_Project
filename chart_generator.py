import matplotlib
matplotlib.use('Agg') # サーバー環境で必須
import matplotlib.pyplot as plt
import numpy as np
import io, base64, os
from matplotlib import font_manager
from rules_db import SCORE_WEIGHTS

def generate_radar_chart(aspect_scores):
    """
    ファッション採点結果をレーダーチャートとして描画し、Base64画像データを返す
    """
    
    # (フォント登録処理は app.py で実行済み)
    
    # ▼▼▼ 修正: {key: value} の辞書(dict)形式 ▼▼▼
    label_map = {
        'color_harmony': '色の調和',
        'fit_and_silhouette': 'シルエット・フィット感',
        'item_coordination': 'アイテムの組み合わせ',
        'cleanliness_material': '清潔感・素材感',
        'accessories_balance': '小物のバランス',
        'trendness': 'トレンド感',
        'tpo_suitability': 'TPO適合度',
        'photogenic_quality': '写真映え'
    }
    # ▲▲▲ 修正 ▲▲▲

    chart_keys = SCORE_WEIGHTS.keys()
    
    labels = [label_map.get(key, key) for key in chart_keys]
    values = [aspect_scores.get(key, 0) for key in chart_keys]

    # ======== 自動スケール調整（項目ごとの満点に合わせる） ========
    max_values = [SCORE_WEIGHTS.get(key, 10.0) for key in chart_keys]
    
    normalized_values = []
    for v, m in zip(values, max_values):
        if m > 0:
            normalized_values.append((v / m) * 100) # 0-100に正規化
        else:
            normalized_values.append(0)

    # ======== レーダーチャート設定 ========
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    normalized_values += normalized_values[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles, normalized_values, color='blue', linewidth=2)
    ax.fill(angles, normalized_values, color='skyblue', alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["25", "50", "75", "100%"], color="grey", size=7)
    ax.set_ylim(0, 100)

    ax.set_title("ファッション採点レーダーチャート", fontsize=14, pad=20)

    # ======== Base64変換 ========
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)

    return f"data:image/png;base64,{chart_base64}"
