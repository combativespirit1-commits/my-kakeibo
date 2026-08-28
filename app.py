import os
from datetime import datetime, date
import pandas as pd
import streamlit as st

# 1. ページ設定
st.set_page_config(
    page_title="Dark Style 家計簿",
    page_icon="💳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

EXCEL_FILE = "kakeibo_data.xlsx"

# カテゴリ大ごとの月間予算設定
BUDGET_MAP = {
    "食費": 40000,
    "外食": 14000,
    "日用品": 35000,
    "交通費（アルファード）": 10000,
    "娯楽": 10000,
    "医療": 5000
}

# カテゴリの連動定義（大カテゴリ ➔ 中カテゴリ）
CATEGORY_MAP = {
    "食費": ["スーパー", "コストコ"],
    "外食": ["外食", "飲み会", "ママ友会"],
    "日用品": ["大人日用品", "子ども日用品"],
    "交通費（アルファード）": ["ガソリン代", "ETC代"],
    "娯楽": ["遊び旅行", "子どもおもちゃ", "被服", "美容院"],
    "医療": ["病院", "動物病院", "コンタクト"]
}

if not os.path.exists(EXCEL_FILE):
    df_init = pd.DataFrame(
        columns=["支払い日", "入力日", "カテゴリ大", "カテゴリ中", "カテゴリ小", "金額", "メモ"]
    )
    df_init.to_excel(EXCEL_FILE, index=False)

# 全体デザイン・高コントラストCSS
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF !important;
    }
    label, p, .stCaption, div[data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    h1 {
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        color: #58A6FF !important;
        text-align: center;
        margin-bottom: 0.8rem !important;
    }
    .stCaption {
        color: #8B949E !important;
    }
    input {
        color: #FFFFFF !important;
        background-color: #161B22 !important;
    }
    div[data-baseweb="input"] {
        background-color: #161B22 !important;
        border-color: #30363D !important;
    }

    /* テンキーボタンCSS */
    div[data-testid="stColumn"] button {
        background-color: #30363D !important;
        color: #FFFFFF !important;
        font-size: 1.3rem !important;
        font-weight: 800 !important;
        border: 1px solid #8B949E !important;
        border-radius: 8px !important;
        height: 3.2rem !important;
    }
    div[data-testid="stColumn"] button:hover {
        background-color: #484F58 !important;
        border-color: #58A6FF !important;
    }

    /* メイン登録ボタン */
    button[kind="primary"] {
        background: linear-gradient(135deg, #1F6FEB 0%, #238636 100%) !important;
        color: #FFFFFF !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        border: none !important;
        height: 3.4rem !important;
    }

    /* 履歴欄（st.expander）の文字視認性 */
    details {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-radius: 8px !important;
        margin-bottom: 8px !important;
    }
    summary {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
    }
    details div[data-testid="stExpanderDetails"] {
        background-color: #0D1117 !important;
        color: #FFFFFF !important;
    }
    details div[data-testid="stExpanderDetails"] * {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("💳 家計簿")

# 全データの読み込み（型を文字列化して安全に読み込み）
df_all = pd.read_excel(EXCEL_FILE, dtype={"支払い日": str, "入力日": str})

# セッション状態の初期化
if "amount_str" not in st.session_state:
    st.session_state["amount_str"] = "0"
if "edit_index" not in st.session_state:
    st.session_state["edit_index"] = None

# --- 1. 日付 & カテゴリ設定 ---
pay_date = st.date_input("🗓️ 支払い日", datetime.now())

# 15日締めロジック
if pay_date.day >= 16:
    if pay_date.month == 12:
        start_date = date(pay_date.year, 12, 16)
        end_date = date(pay_date.year + 1, 1, 15)
    else:
        start_date = date(pay_date.year, pay_date.month, 16)
        end_date = date(pay_date.year, pay_date.month + 1, 15)
    target_period_label = f"{pay_date.month}月分 ({start_date.strftime('%m/%d')}〜{end_date.strftime('%m/%d')})"
else:
    if pay_date.month == 1:
        start_date = date(pay_date.year - 1, 12, 16)
        end_date = date(pay_date.year, 1, 15)
        target_period_label = f"12月分 ({start_date.strftime('%m/%d')}〜{end_date.strftime('%m/%d')})"
    else:
        start_date = date(pay_date.year, pay_date.month - 1, 16)
        end_date = date(pay_date.year, pay_date.month, 15)
        target_period_label = f"{pay_date.month - 1}月分 ({start_date.strftime('%m/%d')}〜{end_date.strftime('%m/%d')})"

# 期間によるフィルタリング
if not df_all.empty and "支払い日" in df_all.columns:
    df_all["支払い日_dt"] = pd.to_datetime(df_all["支払い日"], errors="coerce").dt.date
    df_month = df_all[(df_all["支払い日_dt"] >= start_date) & (df_all["支払い日_dt"] <= end_date)]
else:
    df_month = pd.DataFrame()

st.caption(f"🏷️ カテゴリ選択（対象期間: {target_period_label}）")

cat_large = st.radio(
    "カテゴリ大",
    list(CATEGORY_MAP.keys()),
    horizontal=True
)

selected_budget = BUDGET_MAP.get(cat_large, 0)
if not df_month.empty and "カテゴリ大" in df_month.columns:
    selected_spent = df_month[df_month["カテゴリ大"] == cat_large]["金額"].sum()
else:
    selected_spent = 0

selected_remaining = selected_budget - selected_spent
selected_percent = min(selected_spent / selected_budget, 1.0) if selected_budget > 0 else 0.0

if selected_budget == 0:
    st.caption(f"🎯 **【{cat_large}】({target_period_label})** 支出: ¥{selected_spent:,} (※ 予算未設定)")
elif selected_remaining < 0:
    st.caption(f"🎯 **【{cat_large}】({target_period_label})** 予算: ¥{selected_budget:,} / 支出: ¥{selected_spent:,} (⚠️ 超過: ¥{abs(selected_remaining):,} 円)")
else:
    st.caption(f"🎯 **【{cat_large}】({target_period_label})** 予算: ¥{selected_budget:,} / 支出: ¥{selected_spent:,} (残り: ¥{selected_remaining:,} 円)")

st.progress(selected_percent)

sub_categories = CATEGORY_MAP.get(cat_large, [])
cat_medium = st.radio(
    "カテゴリ中",
    sub_categories,
    horizontal=True
)

cat_small = st.text_input("カテゴリ小 (自由記入)", placeholder="詳細な分類やアイテム名など")

st.markdown("---")

# --- 2. テンキー & 直接入力 セクション ---
st.caption("💵 金額を入力")

input_val = st.number_input(
    "金額（手入力・テンキー連動）",
    min_value=0,
    value=int(st.session_state["amount_str"]),
    step=1
)

if input_val != int(st.session_state["amount_str"]):
    st.session_state["amount_str"] = str(input_val)

def press_num(num_str):
    if st.session_state["amount_str"] == "0":
        st.session_state["amount_str"] = num_str
    elif len(st.session_state["amount_str"]) < 9:
        st.session_state["amount_str"] += num_str

def press_add(val):
    cur = int(st.session_state["amount_str"])
    st.session_state["amount_str"] = str(cur + val)

k1, k2, k3, k4 = st.columns(4)
with k1:
    if st.button("7", use_container_width=True): press_num("7"); st.rerun()
    if st.button("4", use_container_width=True): press_num("4"); st.rerun()
    if st.button("1", use_container_width=True): press_num("1"); st.rerun()
    if st.button("0", use_container_width=True): press_num("0"); st.rerun()

with k2:
    if st.button("8", use_container_width=True): press_num("8"); st.rerun()
    if st.button("5", use_container_width=True): press_num("5"); st.rerun()
    if st.button("2", use_container_width=True): press_num("2"); st.rerun()
    if st.button("00", use_container_width=True):
        if st.session_state["amount_str"] != "0" and len(st.session_state["amount_str"]) <= 7:
            st.session_state["amount_str"] += "00"
            st.rerun()

with k3:
    if st.button("9", use_container_width=True): press_num("9"); st.rerun()
    if st.button("6", use_container_width=True): press_num("6"); st.rerun()
    if st.button("3", use_container_width=True): press_num("3"); st.rerun()
    if st.button("⌫", use_container_width=True):
        if len(st.session_state["amount_str"]) > 1:
            st.session_state["amount_str"] = st.session_state["amount_str"][:-1]
        else:
            st.session_state["amount_str"] = "0"
        st.rerun()

with k4:
    if st.button("C", use_container_width=True):
        st.session_state["amount_str"] = "0"
        st.rerun()
    if st.button("+100", use_container_width=True): press_add(100); st.rerun()
    if st.button("+500", use_container_width=True): press_add(500); st.rerun()
    if st.button("+1k", use_container_width=True): press_add(1000); st.rerun()

# --- 3. メモ & 登録ボタン ---
memo = st.text_input("📝 メモ (任意)", placeholder="店名やその他補足など")

if st.button("💾 記録する", type="primary", use_container_width=True):
    current_amount = int(st.session_state["amount_str"])
    if current_amount > 0:
        entry_date = datetime.now().strftime("%Y-%m-%d")
        pay_date_str = pay_date.strftime("%Y-%m-%d")
        
        new_data = pd.DataFrame(
            [[pay_date_str, entry_date, cat_large, cat_medium, cat_small, current_amount, memo]],
            columns=["支払い日", "入力日", "カテゴリ大", "カテゴリ中", "カテゴリ小", "金額", "メモ"],
        )
        
        existing_df = pd.read_excel(EXCEL_FILE, dtype=str)
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
        updated_df.to_excel(EXCEL_FILE, index=False)
        
        st.success(f"保存完了：[{pay_date_str}] {cat_large} ➔ {cat_medium} - {current_amount:,}円")
        st.session_state["amount_str"] = "0"
        st.rerun()
    else:
        st.warning("金額を入力してください。")

st.divider()

# --- 4. 全カテゴリの「予算 vs 実績」まとめ表示 ---
st.subheader(f"📊 全カテゴリ（{target_period_label}）の予算状況")

total_budget = sum(BUDGET_MAP.values())
if not df_month.empty and "金額" in df_month.columns:
    total_spent = pd.to_numeric(df_month["金額"], errors="coerce").sum()
else:
    total_spent = 0

total_remaining = total_budget - total_spent
total_percent = min(total_spent / total_budget, 1.0) if total_budget > 0 else 0.0

st.markdown("**🏆 期間全体サマリー**")
if total_remaining < 0:
    st.caption(f"総予算: **¥{total_budget:,}** / 総支出: **¥{int(total_spent):,}** (⚠️ 全体超過: **¥{abs(int(total_remaining)):,}** 円)")
else:
    st.caption(f"総予算: **¥{total_budget:,}** / 総支出: **¥{int(total_spent):,}** (全体の残り: **¥{int(total_remaining):,}** 円)")

st.progress(total_percent)
st.markdown("---")

for cat, budget in BUDGET_MAP.items():
    if not df_month.empty and "カテゴリ大" in df_month.columns:
        spent = pd.to_numeric(df_month[df_month["カテゴリ大"] == cat]["金額"], errors="coerce").sum()
    else:
        spent = 0
        
    remaining = budget - spent
    percent = min(spent / budget, 1.0) if budget > 0 else 0.0

    col_name, col_metric = st.columns([1, 2])
    with col_name:
        st.write(f"**{cat}**")
    with col_metric:
        if budget == 0:
            st.caption(f"支出: ¥{int(spent):,} (※ 予算未設定)")
        elif remaining < 0:
            st.caption(f"予算: ¥{budget:,} / 支出: ¥{int(spent):,} (⚠️ 超過: ¥{abs(int(remaining)):,} 円)")
        else:
            st.caption(f"予算: ¥{budget:,} / 支出: ¥{int(spent):,} (残り: ¥{int(remaining):,} 円)")
    
    st.progress(percent)

# --- 5. 履歴（安全な型変換処理を適用） ---
st.divider()
st.subheader("📜 履歴（直近5件）")

if os.path.exists(EXCEL_FILE):
    df_current = pd.read_excel(EXCEL_FILE)
    if not df_current.empty:
        recent_indices = df_current.tail(5).index[::-1]
        
        for idx in recent_indices:
            row = df_current.loc[idx]
            
            # 日付文字列を safe に date オブジェクトに変換
            raw_pay_date = row["支払い日"]
            try:
                parsed_date = pd.to_datetime(raw_pay_date).date()
            except Exception:
                parsed_date = datetime.now().date()

            # 金額を safe に int 変換
            try:
                display_amt = int(row["金額"])
            except Exception:
                display_amt = 0
            
            with st.expander(f"【{parsed_date.strftime('%Y-%m-%d')}】{row['カテゴリ大']} ➔ {row['カテゴリ中']} : ¥{display_amt:,}"):
                
                if st.session_state["edit_index"] == idx:
                    edit_pay_date = st.date_input("支払い日", parsed_date, key=f"edit_date_{idx}")
                    
                    cur_cat_l = str(row["カテゴリ大"]) if pd.notna(row["カテゴリ大"]) else list(CATEGORY_MAP.keys())[0]
                    cat_l_idx = list(CATEGORY_MAP.keys()).index(cur_cat_l) if cur_cat_l in CATEGORY_MAP else 0
                    edit_cat_l = st.selectbox("カテゴリ大", list(CATEGORY_MAP.keys()), index=cat_l_idx, key=f"edit_cat_l_{idx}")
                    
                    sub_cats = CATEGORY_MAP.get(edit_cat_l, [])
                    cur_cat_m = str(row["カテゴリ中"]) if pd.notna(row["カテゴリ中"]) else (sub_cats[0] if sub_cats else "")
                    cat_m_idx = sub_cats.index(cur_cat_m) if cur_cat_m in sub_cats else 0
                    edit_cat_m = st.selectbox("カテゴリ中", sub_cats, index=cat_m_idx, key=f"edit_cat_m_{idx}")
                    
                    edit_cat_s = st.text_input("カテゴリ小", str(row["カテゴリ小"]) if pd.notna(row["カテゴリ小"]) else "", key=f"edit_cat_s_{idx}")
                    edit_amount = st.number_input("金額", value=display_amt, step=100, key=f"edit_amt_{idx}")
                    edit_memo = st.text_input("メモ", str(row["メモ"]) if pd.notna(row["メモ"]) else "", key=f"edit_memo_{idx}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("💾 更新", key=f"save_{idx}"):
                            df_current.loc[idx, "支払い日"] = edit_pay_date.strftime("%Y-%m-%d")
                            df_current.loc[idx, "カテゴリ大"] = edit_cat_l
                            df_current.loc[idx, "カテゴリ中"] = edit_cat_m
                            df_current.loc[idx, "カテゴリ小"] = edit_cat_s
                            df_current.loc[idx, "金額"] = int(edit_amount)
                            df_current.loc[idx, "メモ"] = edit_memo
                            
                            if "支払い日_dt" in df_current.columns:
                                df_current = df_current.drop(columns=["支払い日_dt"])
                                
                            df_current.to_excel(EXCEL_FILE, index=False)
                            st.session_state["edit_index"] = None
                            st.success("更新しました！")
                            st.rerun()
                    with c2:
                        if st.button("❌ キャンセル", key=f"cancel_{idx}"):
                            st.session_state["edit_index"] = None
                            st.rerun()
                
                else:
                    st.markdown(f"**カテゴリ小:** {row['カテゴリ小'] if pd.notna(row['カテゴリ小']) and str(row['カテゴリ小']).strip() != '' else 'なし'}")
                    st.markdown(f"**メモ:** {row['メモ'] if pd.notna(row['メモ']) and str(row['メモ']).strip() != '' else 'なし'}")
                    st.markdown("---")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✏️ 編集する", key=f"edit_btn_{idx}"):
                            st.session_state["edit_index"] = idx
                            st.rerun()
                    with c2:
                        if st.button("🗑️ 削除する", key=f"del_btn_{idx}"):
                            df_current = df_current.drop(idx)
                            if "支払い日_dt" in df_current.columns:
                                df_current = df_current.drop(columns=["支払い日_dt"])
                            df_current.to_excel(EXCEL_FILE, index=False)
                            st.success("削除しました！")
                            st.rerun()

        total_sum = pd.to_numeric(df_current['金額'], errors='coerce').sum()
        st.caption(f"現在の全期間合計支出: {int(total_sum):,} 円")
