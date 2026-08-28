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

BUDGET_MAP = {
    "食費": 40000,
    "外食": 14000,
    "日用品": 35000,
    "交通費（アルファード）": 10000,
    "娯楽": 10000,
    "医療": 5000
}

CATEGORY_MAP = {
    "食費": ["スーパー", "コストコ"],
    "外食": ["外食", "飲み会", "ママ友会"],
    "日用品": ["大人日用品", "子ども日用品"],
    "交通費（アルファード）": ["ガソリン代", "ETC代"],
    "娯楽": ["遊び旅行", "子どもおもちゃ", "被服", "美容院"],
    "医療": ["病院", "動物病院", "コンタクト"]
}

BASE_COLUMNS = ["支払い日", "入力日", "カテゴリ大", "カテゴリ中", "カテゴリ小", "金額", "メモ"]

# データ読み込み（型を完全に固定）
def load_data():
    if not os.path.exists(EXCEL_FILE):
        df_init = pd.DataFrame(columns=BASE_COLUMNS)
        df_init.to_excel(EXCEL_FILE, index=False)
        return df_init
    
    df = pd.read_excel(EXCEL_FILE, dtype=str)
    for col in BASE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[BASE_COLUMNS].fillna("")

# 全体デザインCSS
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF !important; }
    label, p, .stCaption, div[data-testid="stMarkdownContainer"] p { color: #FFFFFF !important; font-weight: 600 !important; }
    h1 { font-size: 1.6rem !important; font-weight: 800 !important; color: #58A6FF !important; text-align: center; margin-bottom: 0.8rem !important; }
    .stCaption { color: #8B949E !important; }
    input { color: #FFFFFF !important; background-color: #161B22 !important; }
    div[data-baseweb="input"] { background-color: #161B22 !important; border-color: #30363D !important; }

    /* テンキーボタン */
    div[data-testid="stColumn"] button {
        background-color: #30363D !important;
        color: #FFFFFF !important;
        font-size: 1.3rem !important;
        font-weight: 800 !important;
        border: 1px solid #8B949E !important;
        border-radius: 8px !important;
        height: 3.2rem !important;
    }
    div[data-testid="stColumn"] button:hover { background-color: #484F58 !important; border-color: #58A6FF !important; }

    /* メイン登録ボタン */
    button[kind="primary"] {
        background: linear-gradient(135deg, #1F6FEB 0%, #238636 100%) !important;
        color: #FFFFFF !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        border: none !important;
        height: 3.4rem !important;
    }

    /* 履歴欄視認性 */
    details { background-color: #161B22 !important; border: 1px solid #30363D !important; border-radius: 8px !important; margin-bottom: 8px !important; }
    summary { color: #FFFFFF !important; font-weight: 700 !important; font-size: 1.05rem !important; }
    details div[data-testid="stExpanderDetails"] { background-color: #0D1117 !important; color: #FFFFFF !important; }
    details div[data-testid="stExpanderDetails"] * { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

st.title("💳 家計簿")

df_all = load_data()

if "amount_str" not in st.session_state:
    st.session_state["amount_str"] = "0"
if "edit_index" not in st.session_state:
    st.session_state["edit_index"] = None

# --- 1. 日付 & カテゴリ設定 ---
pay_date = st.date_input("🗓️ 支払い日", datetime.now().date())

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

if not df_all.empty:
    df_work = df_all.copy()
    df_work["_dt"] = pd.to_datetime(df_work["支払い日"], errors="coerce").dt.date
    df_month = df_work[(df_work["_dt"] >= start_date) & (df_work["_dt"] <= end_date)]
else:
    df_month = pd.DataFrame()

st.caption(f"🏷️ カテゴリ選択（対象期間: {target_period_label}）")

cat_large = st.radio("カテゴリ大", list(CATEGORY_MAP.keys()), horizontal=True)

selected_budget = BUDGET_MAP.get(cat_large, 0)
if not df_month.empty:
    selected_spent = pd.to_numeric(df_month[df_month["カテゴリ大"] == cat_large]["金額"], errors="coerce").fillna(0).sum()
else:
    selected_spent = 0

selected_remaining = selected_budget - selected_spent
selected_percent = min(selected_spent / selected_budget, 1.0) if selected_budget > 0 else 0.0

if selected_budget == 0:
    st.caption(f"🎯 **【{cat_large}】({target_period_label})** 支出: ¥{int(selected_spent):,} (※ 予算未設定)")
elif selected_remaining < 0:
    st.caption(f"🎯 **【{cat_large}】({target_period_label})** 予算: ¥{selected_budget:,} / 支出: ¥{int(selected_spent):,} (⚠️ 超過: ¥{abs(int(selected_remaining)):,} 円)")
else:
    st.caption(f"🎯 **【{cat_large}】({target_period_label})** 予算: ¥{selected_budget:,} / 支出: ¥{int(selected_spent):,} (残り: ¥{int(selected_remaining):,} 円)")

st.progress(selected_percent)

sub_categories = CATEGORY_MAP.get(cat_large, [])
cat_medium = st.radio("カテゴリ中", sub_categories, horizontal=True)
cat_small = st.text_input("カテゴリ小 (自由記入)", placeholder="詳細な分類やアイテム名など")

st.markdown("---")

# --- 2. テンキー & 直接入力 ---
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
            [[pay_date_str, entry_date, cat_large, cat_medium, cat_small, str(current_amount), str(memo)]],
            columns=BASE_COLUMNS
        )
        
        existing_df = load_data()
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
        updated_df[BASE_COLUMNS].to_excel(EXCEL_FILE, index=False)
        
        st.success(f"保存完了：[{pay_date_str}] {cat_large} ➔ {cat_medium} - {current_amount:,}円")
        st.session_state["amount_str"] = "0"
        st.rerun()
    else:
        st.warning("金額を入力してください。")

st.divider()

# --- 4. 予算状況サマリー ---
st.subheader(f"📊 全カテゴリ（{target_period_label}）の予算状況")

total_budget = sum(BUDGET_MAP.values())
if not df_month.empty:
    total_spent = pd.to_numeric(df_month["金額"], errors="coerce").fillna(0).sum()
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
    if not df_month.empty:
        spent = pd.to_numeric(df_month[df_month["カテゴリ大"] == cat]["金額"], errors="coerce").fillna(0).sum()
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

# --- 5. 履歴 & エクスポート ---
st.divider()
st.subheader("📜 履歴（直近5件）")

if os.path.exists(EXCEL_FILE):
    df_current = load_data()
    if not df_current.empty:
        recent_indices = list(df_current.tail(5).index)[::-1]
        
        for idx in recent_indices:
            row = df_current.loc[idx]
            
            raw_date_str = str(row["支払い日"]).split()[0]
            try:
                parsed_date = datetime.strptime(raw_date_str, "%Y-%m-%d").date()
            except Exception:
                parsed_date = datetime.now().date()

            try:
                display_amt = int(float(row["金額"]))
            except Exception:
                display_amt = 0
            
            pay_str = parsed_date.strftime('%Y-%m-%d')
            cat_l_str = str(row['カテゴリ大'])
            cat_m_str = str(row['カテゴリ中'])
            
            with st.expander(f"【{pay_str}】{cat_l_str} ➔ {cat_m_str} : ¥{display_amt:,}"):
                
                if st.session_state["edit_index"] == idx:
                    with st.form(key=f"edit_form_{idx}"):
                        edit_pay_date = st.date_input("支払い日", parsed_date)
                        
                        cat_l_idx = list(CATEGORY_MAP.keys()).index(cat_l_str) if cat_l_str in CATEGORY_MAP else 0
                        edit_cat_l = st.selectbox("カテゴリ大", list(CATEGORY_MAP.keys()), index=cat_l_idx)
                        
                        sub_cats = CATEGORY_MAP.get(edit_cat_l, [])
                        cat_m_idx = sub_cats.index(cat_m_str) if cat_m_str in sub_cats else 0
                        edit_cat_m = st.selectbox("カテゴリ中", sub_cats, index=cat_m_idx)
                        
                        edit_cat_s = st.text_input("カテゴリ小", str(row["カテゴリ小"]))
                        edit_amount = st.number_input("金額", value=display_amt, step=100)
                        edit_memo = st.text_input("メモ", str(row["メモ"]))
                        
                        f_col1, f_col2 = st.columns(2)
                        with f_col1:
                            submit_save = st.form_submit_button("💾 更新")
                        with f_col2:
                            submit_cancel = st.form_submit_button("❌ キャンセル")
                        
                        if submit_save:
                            df_save = load_data()
                            df_save.loc[idx, "支払い日"] = edit_pay_date.strftime("%Y-%m-%d")
                            df_save.loc[idx, "カテゴリ大"] = edit_cat_l
                            df_save.loc[idx, "カテゴリ中"] = edit_cat_m
                            df_save.loc[idx, "カテゴリ小"] = edit_cat_s
                            df_save.loc[idx, "金額"] = str(int(edit_amount))
                            df_save.loc[idx, "メモ"] = edit_memo
                            
                            df_save[BASE_COLUMNS].to_excel(EXCEL_FILE, index=False)
                            st.session_state["edit_index"] = None
                            st.success("更新しました！")
                            st.rerun()
                            
                        if submit_cancel:
                            st.session_state["edit_index"] = None
                            st.rerun()
                
                else:
                    st.markdown(f"**カテゴリ小:** {row['カテゴリ小'] if str(row['カテゴリ小']).strip() != '' else 'なし'}")
                    st.markdown(f"**メモ:** {row['メモ'] if str(row['メモ']).strip() != '' else 'なし'}")
                    st.markdown("---")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✏️ 編集する", key=f"edit_btn_{idx}"):
                            st.session_state["edit_index"] = idx
                            st.rerun()
                    with c2:
                        if st.button("🗑️ 削除する", key=f"del_btn_{idx}"):
                            df_del = load_data()
                            df_del = df_del.drop(idx)
                            df_del[BASE_COLUMNS].to_excel(EXCEL_FILE, index=False)
                            st.success("削除しました！")
                            st.rerun()

        total_sum = pd.to_numeric(df_current['金額'], errors='coerce').fillna(0).sum()
        st.caption(f"現在の全期間合計支出: {int(total_sum):,} 円")

    # 📥 Excelダウンロードボタンの配置
    st.markdown("---")
    with open(EXCEL_FILE, "rb") as f:
        st.download_button(
            label="📥 家計簿データをExcelでダウンロード",
            data=f,
            file_name="kakeibo_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
