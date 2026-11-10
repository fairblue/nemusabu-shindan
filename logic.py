# -*- coding: utf-8 -*-
"""ねむサブ診断 — 計算ロジック（UIから分離し、単体テスト可能にする）

自己申告ベースのサブスク診断。アカウント連携は一切しない。
利用頻度から「眠り金額」（使っていないのに払っている推定額）を算出する。
"""

# 利用頻度ごとの「眠り率」: その金額のうち、使われずに眠っている割合の推定
USAGE_SLEEP_RATE = {
    "毎日使う": 0.0,
    "週に数回": 0.3,
    "月に数回": 0.7,
    "ほとんど使っていない": 1.0,
}
USAGE_OPTIONS = list(USAGE_SLEEP_RATE.keys())

# カタログ: (サービス名, カテゴリ, 月額換算・税込の目安円)
CATALOG = [
    # 動画配信
    ("Netflix（スタンダード）", "動画配信", 1590),
    ("Amazon Prime", "動画配信", 600),
    ("Hulu", "動画配信", 1026),
    ("U-NEXT", "動画配信", 2189),
    ("Disney+", "動画配信", 990),
    ("YouTube Premium", "動画配信", 1280),
    ("dアニメストア", "動画配信", 550),
    # 音楽
    ("Spotify Premium", "音楽", 980),
    ("Apple Music", "音楽", 1080),
    ("LINE MUSIC", "音楽", 980),
    ("AWA", "音楽", 960),
    # 本・マンガ
    ("Kindle Unlimited", "本・マンガ", 980),
    ("dマガジン", "本・マンガ", 580),
    ("楽天マガジン", "本・マンガ", 597),
    ("コミックシーモア読み放題ライト", "本・マンガ", 780),
    # ゲーム
    ("Nintendo Switch Online", "ゲーム", 306),
    ("PlayStation Plus Essential", "ゲーム", 850),
    ("Xbox Game Pass Ultimate", "ゲーム", 1550),
    ("Apple Arcade", "ゲーム", 900),
    # 学習
    ("スタディサプリ", "学習", 2178),
    ("Duolingo Super", "学習", 1100),
    ("Schoo", "学習", 980),
    ("ドットインストール プレミアム", "学習", 1080),
    # クラウド・AI・仕事
    ("iCloud+（50GB）", "クラウド・AI・仕事", 180),
    ("Google One（100GB）", "クラウド・AI・仕事", 250),
    ("Dropbox Plus", "クラウド・AI・仕事", 1512),
    ("Notion Plus", "クラウド・AI・仕事", 1650),
    ("ChatGPT Plus", "クラウド・AI・仕事", 3000),
    # 健康・生活
    ("chocoZAP", "健康・生活", 3278),
    ("エニタイムフィットネス", "健康・生活", 7480),
    ("クックパッドプレミアム", "健康・生活", 308),
    # ニュース・家計
    ("NewsPicks", "ニュース・家計", 1700),
    ("日本経済新聞 電子版", "ニュース・家計", 4277),
    ("マネーフォワード ME プレミアム", "ニュース・家計", 550),
]

CATEGORIES = []
for _name, _cat, _price in CATALOG:
    if _cat not in CATEGORIES:
        CATEGORIES.append(_cat)


def monthly_equivalent(price: int, cycle: str) -> int:
    """課金サイクルを月額換算する。cycle は '月額' か '年額'。"""
    if price < 0:
        raise ValueError("金額は0以上で入力してください")
    if cycle == "年額":
        return round(price / 12)
    return price


def diagnose(entries):
    """診断を実行する。

    entries: [{"name": str, "category": str, "monthly": int, "usage": str}, ...]
             monthly は月額換算済みの金額。
    戻り値: dict（合計・眠り金額・スコア・グレード・カテゴリ別・解約候補）
    """
    total_monthly = 0
    sleeping_monthly = 0
    by_category = {}
    candidates = []
    for e in entries:
        monthly = int(e["monthly"])
        rate = USAGE_SLEEP_RATE[e["usage"]]
        sleeping = round(monthly * rate)
        total_monthly += monthly
        sleeping_monthly += sleeping
        cat = by_category.setdefault(
            e["category"], {"monthly": 0, "sleeping": 0, "count": 0}
        )
        cat["monthly"] += monthly
        cat["sleeping"] += sleeping
        cat["count"] += 1
        if rate >= 0.7:
            candidates.append(
                {
                    "name": e["name"],
                    "monthly": monthly,
                    "sleeping": sleeping,
                    "usage": e["usage"],
                    "annual_saving": monthly * 12,  # 解約で浮くのは支払全額
                }
            )
    candidates.sort(key=lambda c: c["sleeping"], reverse=True)

    score, grade = health_score(total_monthly, sleeping_monthly, len(entries))
    return {
        "count": len(entries),
        "total_monthly": total_monthly,
        "total_annual": total_monthly * 12,
        "sleeping_monthly": sleeping_monthly,
        "sleeping_annual": sleeping_monthly * 12,
        "sleeping_ratio": (sleeping_monthly / total_monthly) if total_monthly else 0.0,
        "score": score,
        "grade": grade,
        "by_category": by_category,
        "candidates": candidates,
    }


def health_score(total_monthly: int, sleeping_monthly: int, count: int) -> tuple:
    """健全度スコア（0〜100）とグレード（S〜D）。

    眠り率が高いほど減点し、契約数が多すぎる場合も少しずつ減点する。
    """
    if total_monthly <= 0:
        return 100, "S"
    ratio = sleeping_monthly / total_monthly
    score = 100 - ratio * 80 - max(0, count - 8) * 2
    score = max(0, min(100, round(score)))
    if score >= 90:
        grade = "S"
    elif score >= 75:
        grade = "A"
    elif score >= 60:
        grade = "B"
    elif score >= 45:
        grade = "C"
    else:
        grade = "D"
    return score, grade


def share_text(result: dict) -> str:
    """X共有用の結果テキストを生成する。"""
    lines = [
        "【ねむサブ診断】",
        f"契約中のサブスク：{result['count']}件 / 月額合計 ¥{result['total_monthly']:,}",
        f"眠っている金額：月 ¥{result['sleeping_monthly']:,}（年 ¥{result['sleeping_annual']:,}）",
        f"健全度スコア：{result['score']}点（グレード {result['grade']}）",
    ]
    if result["candidates"]:
        top = result["candidates"][0]
        lines.append(
            f"見直し候補トップ：{top['name']}（年 ¥{top['annual_saving']:,} の節約余地）"
        )
    lines.append("#ねむサブ診断 #サブスク見直し")
    return "\n".join(lines)
