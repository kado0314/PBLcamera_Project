import base64
from flask import Blueprint, render_template, request
from .scorer_main import FashionScorer
from .chart_generator import generate_radar_chart

scoring_bp = Blueprint("scoring", __name__, template_folder="templates")

@scoring_bp.route("/", methods=["GET"])
def index():
    """採点ページを表示"""
    # ▼▼▼ 修正: ページの初期表示時にデフォルトの選択値を渡す ▼▼▼
    return render_template("saiten.html", uploaded_image_data=False, selected_gender="neutral", selected_scene="date", score=None)

@scoring_bp.route("/saiten", methods=["GET", "POST"])
def saiten():
    if request.method == "GET":
        # 初回アクセス時に採点フォームを表示
        return render_template(
            "saiten.html",
            uploaded_image_data=False,
            selected_gender="neutral",
            selected_scene="date",
            score=None
        )
        
    image_file = request.files.get("image_file")

    # ▼▼▼ 修正: フォームからデータを取得。値がない場合はデフォルト値を設定 ▼▼▼
    user_gender = request.form.get("user_gender", "neutral")
    intended_scene = request.form.get("intended_scene", "date")
    # ▲▲▲ 修正 ▲▲▲

    if not image_file:
        # 画像がない場合でも、フォームの選択状態を維持してページを再表示
        return render_template(
            "saiten.html", 
            score=None, 
            feedback=["画像がアップロードされていません。"],
            selected_gender=user_gender,
            selected_scene=intended_scene
        )

    # 画像をBase64化
    image_data = base64.b64encode(image_file.read()).decode("utf-8")
    
    # ▼▼▼ 修正: ハードコーディングされていた箇所をフォームの値で置き換え ▼▼▼
    
    # 1. FashionScorerの初期化にフォームの性別を渡す
    scorer = FashionScorer(user_gender=user_gender)
    
    # 2. analyzeメソッドのメタデータにもフォームの値を渡す
    metadata = {
        "user_locale": "ja-JP", 
        "intended_scene": intended_scene,
        "user_gender": user_gender # scorer_main.pyのanalyzeメソッド内でも参照するため
    }
    result = scorer.analyze(image_data, metadata)
    # ▲▲▲ 修正 ▲▲▲

    # --- subscores を安全に取得 ---
    aspect_scores = result.get("subscores", None)
    if not aspect_scores:
        print("⚠️ subscores が見つかりません。結果:", result)
        aspect_scores = {
            "color_harmony": 0,
            "fit_and_silhouette": 0,
            "item_coordination": 0,
            "cleanliness_material": 0,
            "accessories_balance": 0,
            "trendness": 0,
            "tpo_suitability": 0,
            "photogenic_quality": 0
        }

    radar_chart_data = generate_radar_chart(aspect_scores)

    return render_template(
        "saiten.html",
        uploaded_image_data=f"data:image/png;base64,{image_data}",
        score=result.get("overall_score", "N/A"),
        recommendation="あなたのコーディネートをさらに引き立てるポイントがあります！",
        feedback=result.get("explanations", ["詳細な説明はありません。"]),
        radar_chart_data=radar_chart_data,
        # ▼▼▼ 修正: 採点結果とともに、フォームの選択状態を維持する ▼▼▼
        selected_gender=user_gender,
        selected_scene=intended_scene
    )
