# -*- coding: utf-8 -*-
"""ねむサブ診断 — Streamlit UI

契約中のサブスクを自己申告で選ぶだけ。アカウント連携なし、データは保存しない。
"""
import pandas as pd
import streamlit as st

from logic import (
    CATALOG,
    CATEGORIES,
    USAGE_OPTIONS,
    diagnose,
    monthly_equivalent,
    share_text,
)

st.set_page_config(page_title="ねむサブ診断", page_icon="💤", layout="centered")

st.title("💤 ねむサブ診断")
st.write(
    "契約中のサブスクを選んで、使っている頻度を答えるだけ。"
    "眠っている（使っていないのに払っている）金額と、サブスクの健全度を約30秒で診断します。"
)
st.caption(
    "※ アカウント連携は一切しません。入力した内容はこの画面の中だけで使われ、保存・送信されません。金額は税込の目安です。"
)

if "custom_entries" not in st.session_state:
    st.session_state.custom_entries = []

# --- 1. カタログから選ぶ ---
st.header("1. 契約中のサブスクを選ぶ")
selected = []
for cat in CATEGORIES:
    items = [(name, price) for name, c, price in CATALOG if c == cat]
    with st.expander(f"{cat}（{len(items)}件）"):
        for name, price in items:
            if st.checkbox(f"{name} — 月額 ¥{price:,}", key=f"chk::{name}"):
                usage = st.selectbox(
                    f"{name} の利用頻度",
                    USAGE_OPTIONS,
                    index=1,
                    key=f"use::{name}",
                )
                selected.append(
                    {"name": name, "category": cat, "monthly": price, "usage": usage}
                )

# --- 2. カタログにないサブスクを追加 ---
st.header("2. カタログにないサブスクを追加")
with st.form("custom_form", clear_on_submit=True):
    c1, c2 = st.columns([2, 1])
    custom_name = c1.text_input("サービス名")
    custom_price = c2.number_input("金額（円）", min_value=0, step=100, value=0)
    c3, c4 = st.columns(2)
    custom_cycle = c3.selectbox("課金サイクル", ["月額", "年額"])
    custom_usage = c4.selectbox("利用頻度", USAGE_OPTIONS, index=1)
    submitted = st.form_submit_button("追加する")
    if submitted:
        if custom_name.strip() and custom_price > 0:
            st.session_state.custom_entries.append(
                {
                    "name": custom_name.strip(),
                    "category": "カスタム",
                    "monthly": monthly_equivalent(int(custom_price), custom_cycle),
                    "usage": custom_usage,
                }
            )
        else:
            st.warning("サービス名と金額（1円以上）を入力してください。")

if st.session_state.custom_entries:
    st.write("追加済み：")
    for i, e in enumerate(st.session_state.custom_entries):
        col_a, col_b = st.columns([4, 1])
        col_a.write(f"・{e['name']} — 月額換算 ¥{e['monthly']:,}（{e['usage']}）")
        if col_b.button("削除", key=f"del::{i}"):
            st.session_state.custom_entries.pop(i)
            st.rerun()

entries = selected + st.session_state.custom_entries

# --- 3. 診断結果 ---
st.header("3. 診断結果")
if not entries:
    st.info("サブスクを1つ以上選ぶと、ここに診断結果が表示されます。")
else:
    result = diagnose(entries)

    m1, m2, m3 = st.columns(3)
    m1.metric("契約件数", f"{result['count']} 件")
    m2.metric("月額合計", f"¥{result['total_monthly']:,}")
    m3.metric("年額合計", f"¥{result['total_annual']:,}")

    st.subheader(f"健全度スコア：{result['score']} 点（グレード {result['grade']}）")
    st.progress(result["score"] / 100)

    st.error(
        f"💤 眠っている金額：月 ¥{result['sleeping_monthly']:,}（年 ¥{result['sleeping_annual']:,}）"
        f" — 支払額の {result['sleeping_ratio'] * 100:.0f}% が使われていない計算です"
    )

    st.subheader("カテゴリ別の内訳")
    df = pd.DataFrame(
        [
            {
                "カテゴリ": cat,
                "件数": v["count"],
                "月額": v["monthly"],
                "うち眠り金額": v["sleeping"],
            }
            for cat, v in result["by_category"].items()
        ]
    ).sort_values("月額", ascending=False)
    st.dataframe(df, hide_index=True, width="stretch")
    st.bar_chart(df.set_index("カテゴリ")[["月額", "うち眠り金額"]])

    st.subheader("解約・見直し候補")
    if result["candidates"]:
        for c in result["candidates"]:
            st.write(
                f"- **{c['name']}**（{c['usage']}）— 月 ¥{c['monthly']:,}、"
                f"解約すると年 ¥{c['annual_saving']:,} の節約余地"
            )
    else:
        st.success("いまのところ、ほとんど使っていないサブスクはありません。この調子です。")

    st.subheader("結果をXで共有する")
    text = share_text(result)
    st.text_area("共有テキスト（コピーして使えます）", value=text, height=140)
    st.caption("ねむサブ診断 https://nemusabu-shindan.onrender.com")

st.divider()
st.caption(
    "ねむサブ診断 — 金額は各サービスの一般的なプランの目安で、実際の請求額と異なる場合があります。"
    "眠り金額は利用頻度からの推定です。"
)
