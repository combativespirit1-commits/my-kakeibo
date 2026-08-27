import os
from datetime import datetime
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
    "外食": 28000,
    "日用品": 30000,
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

# 全体デザイン＆テンキー安全スタイリング
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
    .amount-display {
        background: linear-gradient(135deg, #161B22 0%, #0D1117 100%);
        border: 1.5px solid #58A6FF;
        box-shadow: 0px 0px 8px rgba(88, 166, 255, 0.2);
        border-radius: 10px;
        padding: 8px 12px;
        text-align: right;
        font-size: 1.8rem;
        font-weight: 800;
        color: #58A6FF !important;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }

    /* テンキー専用コンテナ設定（他のエレメントに影響を与えない） */
    .keypad-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 6px;
        width: 100%;
        max-width: 400px;
        margin: 0 auto 15px auto;
    }
    
    /* テンキーボタンCSS */
    .keypad-btn {
        width: 100%;
        height: 48px;
        font-size: 1rem;
        font-weight: bold;
        color: #FFFFFF;
        background-color: #21262D;
        border: 1px solid #454C54;
        border-radius: 8px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        user-select: none;
        -webkit-tap-highlight-color: transparent;
    }
    .keypad-btn:active {
        background-color: #30363D;
        border-color: #58A6FF;
        color: #58A6FF;
    }
    .keypad-btn-clear {
        background-color: #361f22;
        border-color: #6e2c31;
        color: #ff7b72;
    }
    
    button[kind="primary"] {
        background: linear-gradient(135deg, #1F6FEB 0%, #238636 100%) !important;
        color: #FFFFFF !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        border: none !important;
        height: 3.2rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("💳 家計簿")

# 当月データの自動集計処理
df_all = pd.read_excel(EXCEL_FILE)
now = datetime.now()
current_month_str = now.strftime("%Y-%m")

if not df_all.empty and "支払い日" in df_all.columns:
    df_all["支払い日_dt"] = pd.to_datetime(df_all["支払い日"], errors="coerce")
    df_month = df_all[df_all["支払い日_dt"].dt.strftime("%Y-%m") == current_month_str]
else:
    df_month = pd.DataFrame()

# セッション状態の初期化
if "amount_str" not in st.session_state:
    st.session_state["amount_str"] = "0"

# テンキー操作用クエリパラメータ処理（JavaScript連動用）
query_params = st.query_params
if "action" in query_params:
    action = query_params["action"]
    st.query_params.clear()
    
    if action.startswith("num_"):
        num = action.replace("num_", "")
        if st.session_state["amount_str"] == "0":
            st.session_state["amount_str"] = num
        elif len(st.session_state["amount_str"]) < 9:
            st.session_state["amount_str"] += num
    elif action == "00":
        if st.session_state["amount_str"] != "0" and len(st.session_state["amount_str"]) <= 7:
            st.session_state["amount_str"] += "00"
    elif action == "clear":
        st.session_state["amount_str"] = "0"
    elif action == "back":
        if len(st.session_state["amount_str"]) > 1:
            st.session_state["amount_str"] = st.session_state["amount_str"][:-1]
        else:
            st.session_state["amount_str"] = "0"
    elif action.startswith("add_"):
        add_val = int(action.replace("add_", ""))
        cur = int(st.session_state["amount_str"])
        st.session_state["amount_str"] = str(cur + add_val)
    st.rerun()

# --- 1. 日付 & カテゴリ設定 ---
pay_date = st.date_input("🗓️ 支払い日", datetime.now())

st.caption("🏷️ カテゴリ選択")

cat_large = st.radio(
    "カテゴリ大",
    list(CATEGORY_MAP.keys()),
    horizontal=True
)

# 選択中のカテゴリ大の「予算 vs 実績」プログレスバー表示
selected_budget = BUDGET_MAP.get(cat_large, 0)
if not df_month.empty and "カテゴリ大" in df_month.columns:
    selected_spent = df_month[df_month["カテゴリ大"] == cat_large]["金額"].sum()
else:
    selected_spent = 0

selected_remaining = selected_budget - selected_spent
selected_percent = min(selected_spent / selected_budget, 1.0) if selected_budget > 0 else 0.0

if selected_budget == 0:
    st.caption(f"🎯 **【{cat_large}】** 支出: ¥{selected_spent:,} (※ 予算未設定)")
elif selected_remaining < 0:
    st.caption(f"🎯 **【{cat_large}】** 予算: ¥{selected_budget:,} / 支出: ¥{selected_spent:,} (⚠️ 超過: ¥{abs(selected_remaining):,} 円)")
else:
    st.caption(f"🎯 **【{cat_large}】** 予算: ¥{selected_budget:,} / 支出: ¥{selected_spent:,} (残り: ¥{selected_remaining:,} 円)")

st.progress(selected_percent)

# カテゴリ中の選択
sub_categories = CATEGORY_MAP.get(cat_large, [])
cat_medium = st.radio(
    "カテゴリ中",
    sub_categories,
    horizontal=True
)

cat_small = st.text_input("カテゴリ小 (自由記入)", placeholder="詳細な分類やアイテム名など")

st.markdown("---")

# --- 2. 電卓風 金額入力セクション ---
st.caption("💵 金額を入力")

current_amount = int(st.session_state["amount_str"])
st.markdown(f'<div class="amount-display">¥ {current_amount:,}</div>', unsafe_allow_html=True)

# 完全分離型のHTML+CSSテンキー（PC・スマホ双方で完全に独立・崩れない設計）
st.markdown("""
<div class="keypad-container">
    <div class="keypad-btn" onclick="window.location.search='?action=num_7'">7</div>
    <div class="keypad-btn" onclick="window.location.search='?action=num_8'">8</div>
    <div class="keypad-btn" onclick="window.location.search='?action=num_9'">9</div>
    <div class="keypad-btn keypad-btn-clear" onclick="window.location.search='?action=clear'">C</div>
    <div class="keypad-btn" onclick="window.location.search='?action=num_4'">4</div>
    <div class="keypad-btn" onclick="window.location.search='?action=num_5'">5</div>
    <div class="keypad-btn" onclick="window.location.search='?action=num_6'">6</div>
    <div class="keypad-btn" onclick="window.location.search='?action=add_100'">+100</div>
    <div class="keypad-btn" onclick="window.location.search='?action=num_1'">1</div>
    <div class="keypad-btn" onclick="window.location.search='?action=num_2'">2</div>
    <div class="keypad-btn" onclick="window.location.search='?action=num_3'">3</div>
    <div class="keypad-btn" onclick="window.location.search='?action=add_500'">+500</div>
    <div class="keypad-btn" onclick="window.location.search='?action=num_0'">0</div>
    <div class="keypad-btn" onclick="window.location.search='?action=00'">00</div>
    <div class="keypad-btn" onclick="window.location.search='?action=back'">⌫</div>
    <div class="keypad-btn" onclick="window.location.search='?action=add_1000'">+1k</div>
</div>
""", unsafe_allow_html=True)

# --- 3. メモ & 登録ボタン ---
memo = st.text_input("📝 メモ (任意)", placeholder="店名やその他補足など")

if st.button("💾 記録する", type="primary", use_container_width=True):
    if current_amount > 0:
        entry_date = datetime.now().strftime("%Y-%m-%d")
        
        new_data = pd.DataFrame(
            [[pay_date, entry_date, cat_large, cat_medium, cat_small, current_amount, memo]],
            columns=["支払い日", "入力日", "カテゴリ大", "カテゴリ中", "カテゴリ小", "金額", "メモ"],
        )
        
        existing_df = pd.read_excel(EXCEL_FILE)
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
        updated_df.to_excel(EXCEL_FILE, index=False)
        
        st.success(f"保存完了：[{pay_date}] {cat_large} ➔ {cat_medium} - {current_amount:,}円")
        st.session_state["amount_str"] = "0"
        st.rerun()
    else:
        st.warning("金額を入力してください。")

st.divider()

# --- 4. 【下段】全カテゴリの「予算 vs 実績」まとめ表示 ---
st.subheader(f"📊 全カテゴリ今月 ({now.strftime('%Y年%m月')}) の予算状況")

for cat, budget in BUDGET_MAP.items():
    if not df_month.empty and "カテゴリ大" in df_month.columns:
        spent = df_month[df_month["カテゴリ大"] == cat]["金額"].sum()
    else:
        spent = 0
        
    remaining = budget - spent
    percent = min(spent / budget, 1.0) if budget > 0 else 0.0

    col_name, col_metric = st.columns([1, 2])
    with col_name:
        st.write(f"**{cat}**")
    with col_metric:
        if budget == 0:
            st.caption(f"支出: ¥{spent:,} (※ 予算未設定)")
        elif remaining < 0:
            st.caption(f"予算: ¥{budget:,} / 支出: ¥{spent:,} (⚠️ 超過: ¥{abs(remaining):,} 円)")
        else:
            st.caption(f"予算: ¥{budget:,} / 支出: ¥{spent:,} (残り: ¥{remaining:,} 円)")
    
    st.progress(percent)

# --- 5. 履歴（直近5件） ---
st.divider()
st.subheader("📜 履歴（直近5件）")
if os.path.exists(EXCEL_FILE):
    df_current = pd.read_excel(EXCEL_FILE)
    if not df_current.empty:
        show_cols = [c for c in df_current.columns if c != "支払い日_dt"]
        st.dataframe(df_current[show_cols].tail(5), use_container_width=True)
        st.caption(f"現在の全期間合計支出: {df_current['金額'].sum():,} 円")