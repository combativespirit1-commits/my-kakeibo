import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st

# ==========================================
# 1. ページ基本設定・タイトル
# ==========================================
st.set_page_config(
    page_title="家計簿入力アプリ",
    page_icon="💰",
    layout="centered"
)

st.title("家計簿入力アプリ")

# ==========================================
# 2. カテゴリ定義（大 ＞ 中）
# ==========================================
CATEGORY_MAP = {
    "食費": [
        "ドンキ",
        "コープ",
        "コストコ"
    ],
    "外食": [
        "外食",
        "コンビニ",
        "パン屋",
        "ママ友会"
    ],
    "日用品": [
        "ドラッグストア",
        "100均",
        "ホームセンター",
        "その他"
    ],
    "固定費": [
        "電気代",
        "ガス代",
        "水道代",
        "通信費",
        "家賃・ローン",
        "保険"
    ],
    "交通費": [
        "電車・バス",
        "ガソリン",
        "高速・駐車場"
    ],
    "娯楽・教養": [
        "レジャー",
        "書籍",
        "サブスク"
    ],
    "その他": [
        "雑費",
        "特別費"
    ]
}

# ==========================================
# 3. Googleスプレッドシート接続処理
# ==========================================
@st.cache_resource
def get_gspread_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    if "gcp_service_account" in st.secrets:
        if isinstance(st.secrets["gcp_service_account"], dict):
            creds_dict = dict(st.secrets["gcp_service_account"])
        else:
            raw_secrets = str(st.secrets["gcp_service_account"])
            creds_dict = json.loads(raw_secrets, strict=False)
        
        # private_key 内の改行コード補正
        if "private_key" in creds_dict:
            pk = creds_dict["private_key"]
            pk = pk.replace("\\n", "\n")
            creds_dict["private_key"] = pk
            
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # ローカル開発用
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials.json", scope
        )
    return gspread.authorize(creds)

# ==========================================
# 4. 入力フォーム画面
# ==========================================
st.subheader("📝 支出の入力")

with st.form("kakeibo_form", clear_on_submit=True):
    # 日付選択
    date = st.date_input("日付")
    
    # カテゴリ（大）選択
    cat_large = st.selectbox("カテゴリ（大）", list(CATEGORY_MAP.keys()))
    
    # 選択されたカテゴリ（大）に応じたカテゴリ（中）の動的切り替え
    cat_medium_options = CATEGORY_MAP.get(cat_large, ["その他"])
    cat_medium = st.selectbox("カテゴリ（中）", cat_medium_options)
    
    # 金額入力
    amount = st.number_input("金額 (円)", min_value=0, step=100, value=0)
    
    # 備考入力
    memo = st.text_input("メモ・詳細（任意）")
    
    # 送信ボタン
    submitted = st.form_submit_button("スプレッドシートに保存")

# ==========================================
# 5. データ保存処理
# ==========================================
if submitted:
    if amount <= 0:
        st.warning("金額を1円以上で入力してください。")
    else:
        try:
            gc = get_gspread_client()
            
            # スプレッドシート名（※実際のシート名に書き換えてください）
            # もし「家計簿」という名前のシートであればそのまま使えます
            spreadsheet = gc.open("家計簿")
            worksheet = spreadsheet.sheet1
            
            # 追記データを作成（日付, カテゴリ大, カテゴリ中, 金額, メモ）
            new_row = [
                str(date),
                cat_large,
                cat_medium,
                amount,
                memo
            ]
            
            # スプレッドシートの最終行に追加
            worksheet.append_row(new_row)
            
            st.success(f"✅ 保存しました！ 【{cat_large} - {cat_medium}】 : {amount:,}円")
            
        except Exception as e:
            st.error(f"スプレッドシートへの保存に失敗しました: {e}")
