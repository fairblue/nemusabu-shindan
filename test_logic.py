# -*- coding: utf-8 -*-
"""logic.py の単体検証（streamlit不要、素のpythonで実行できる）"""
from logic import (
    CATALOG,
    CATEGORIES,
    diagnose,
    health_score,
    monthly_equivalent,
    share_text,
)

# カタログ: 34件・8カテゴリ・重複名なし・金額は正
assert len(CATALOG) == 34, len(CATALOG)
assert len(CATEGORIES) == 8, CATEGORIES
assert len({n for n, _, _ in CATALOG}) == 34
assert all(p > 0 for _, _, p in CATALOG)
print("catalog OK: 34 items / 8 categories")

# 年額→月額換算
assert monthly_equivalent(11880, "年額") == 990
assert monthly_equivalent(980, "月額") == 980
print("monthly_equivalent OK")

# サンプル診断
entries = [
    {"name": "Netflix（スタンダード）", "category": "動画配信", "monthly": 1590, "usage": "週に数回"},
    {"name": "U-NEXT", "category": "動画配信", "monthly": 2189, "usage": "ほとんど使っていない"},
    {"name": "Spotify Premium", "category": "音楽", "monthly": 980, "usage": "毎日使う"},
    {"name": "Kindle Unlimited", "category": "本・マンガ", "monthly": 980, "usage": "ほとんど使っていない"},
    {"name": "PlayStation Plus Essential", "category": "ゲーム", "monthly": 850, "usage": "月に数回"},
    {"name": "Xbox Game Pass Ultimate", "category": "ゲーム", "monthly": 1850, "usage": "ほとんど使っていない"},
    {"name": "スタディサプリ", "category": "学習", "monthly": 2178, "usage": "月に数回"},
    {"name": "日本経済新聞 電子版", "category": "ニュース・家計", "monthly": 4277, "usage": "週に数回"},
]
r = diagnose(entries)
# 眠り(項目ごとにround): 1590*.3=477, 2189, 0, 980, 850*.7=595, 1850, 2178*.7=1524.6->1525, 4277*.3=1283.1->1283
# 合計 = 477+2189+0+980+595+1850+1525+1283 = 8899
assert r["total_monthly"] == sum(e["monthly"] for e in entries) == 14894, r["total_monthly"]
assert r["total_annual"] == r["total_monthly"] * 12
assert r["sleeping_annual"] == r["sleeping_monthly"] * 12
assert r["sleeping_monthly"] == 8899, r["sleeping_monthly"]
assert r["candidates"][0]["name"] == "U-NEXT"
assert r["candidates"][0]["annual_saving"] == 2189 * 12  # 解約節約額は支払全額×12
assert (r["score"], r["grade"]) == (52, "C")  # 元構築時の目安 51/C と整合する水準
assert 0 <= r["score"] <= 100 and r["grade"] in "SABCD"
print(
    f"sample diagnose OK: monthly=¥{r['total_monthly']:,} sleeping=¥{r['sleeping_monthly']:,}/mo "
    f"(¥{r['sleeping_annual']:,}/yr) score={r['score']} grade={r['grade']}"
)

# スコア境界
assert health_score(0, 0, 0) == (100, "S")
s, g = health_score(10000, 10000, 3)
assert s == 20 and g == "D", (s, g)
s, g = health_score(10000, 0, 5)
assert s == 100 and g == "S", (s, g)
print("health_score boundaries OK")

# グレード境界とペナルティ
assert health_score(10000, 1250, 3)[1] == "S"   # ratio .125 -> 90
assert health_score(10000, 3125, 3)[1] == "A"   # ratio .3125 -> 75
assert health_score(10000, 5000, 3)[1] == "B"   # ratio .5 -> 60
assert health_score(10000, 6875, 3)[1] == "C"   # ratio .6875 -> 45
assert health_score(10000, 0, 12)[0] == 92      # 9件以上は1件ごと-2点
assert monthly_equivalent(10000, "年額") == 833  # 年額換算の丸め
try:
    monthly_equivalent(-1, "月額")
    raise AssertionError("negative price must raise")
except ValueError:
    pass
print("extra boundary tests OK")

# 空入力でも落ちない
r0 = diagnose([])
assert r0["count"] == 0 and r0["total_monthly"] == 0 and r0["score"] == 100
print("empty input OK")

# 共有テキストに主要数値が入る
t = share_text(r)
assert "¥" in t and str(r["score"]) in t and "#ねむサブ診断" in t
print("share_text OK")
print("ALL TESTS PASSED")
