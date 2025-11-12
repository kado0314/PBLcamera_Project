import matplotlib
matplotlib.use('Agg') # ★ デプロイ環境でGUIバックエンドがないため必須
import matplotlib.pyplot as plt
import numpy as np
import io, base64, os
from matplotlib import font_manager
from rules_db import SCORE_WEIGHTS

def generate_radar_chart(aspect_scores):
    # (フォント登録処理は app.py に移管済み)
    
    label_map = { ... } # (前の手順と同じ)
    chart_keys = SCORE_WEIGHTS.keys()
    labels = [label_map.get(key, key) for key in chart_keys]
    values = [aspect_scores.get(key, 0) for key in chart_keys]
    max_values = [SCORE_WEIGHTS.get(key, 10.0) for key in chart_keys]
    
    normalized_values = []
    for v, m in zip(values, max_values):
        if m > 0:
            normalized_values.append((v / m) * 100)
        else:
            normalized_values.append(0)

    # ( ... レーダーチャート設定 ... )
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

    # ( ... Base64変換 ... )
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{chart_base64}"
