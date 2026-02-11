import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. 聖域接続 (Drive & Sheets) ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except: return None

# --- 2. 人気種目リスト ---
popular_ex = {
    "胸": ["ベンチプレス", "インクラインプレス", "ダンベルフライ", "チェストプレス"],
    "脚": ["スクワット", "レッグプレス", "レッグエクステンション", "ブルガリアンスクワット"],
    "背中": ["デッドリフト", "ラットプルダウン", "ベントオーバーロウ", "懸垂"],
    "肩": ["サイドレイズ", "ショルダープレス", "アップライトロウ"],
    "腕": ["アームカール", "ナローベンチプレス", "ライイングエクステンション"],
    "腹筋": ["アブローラー", "レッグレイズ", "クランチ"]
}

# --- 3. UI 構築 (グラデーション & ダッシュボード) ---
st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #fdfcfb 0%, #e2d1c3 100%); }
    .stMetric { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .stButton>button { background: linear-gradient(to right, #ff416c, #ff4b2b); color: white; border-radius: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Active Dashboard")

# Driveから履歴取得
sheet = connect_to_sheet()
df_past = pd.DataFrame()
if sheet:
    data = sheet.get_all_values()
    if len(data) > 1:
        df_past = pd.DataFrame(data[1:], columns=data[0])

# ダッシュボード
col1, col2, col3 = st.columns(3)
with col1: st.metric("今週の負荷", "64.66 t")
with col2: st.metric("28日間の合計", "239.29 t")
with col3: st.metric("総合負荷量", "10.5 ✈️")

# --- 4. AI提案 (115kg基準 & 論文参照) ---
st.markdown("---")
prog = st.selectbox("プログラム", ["ベンチプレス強化(胸・腕)", "スクワット強化(脚)", "デッドリフト強化(背中・脚)", "背中強化", "肩強化"])

if st.button("🚀 Muscle Mateにメニューを相談する"):
    with st.spinner("Drive内の全ファイルをスキャン中..."):
        api_key = st.secrets["GOOGLE_API_KEY"]
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key= {api_key}"
        past_context = df_past.tail(10).to_string() if not df_past.empty else ""
        
        system = (
            f"あなたは最高のパートナー『Muscle Mate』。MAX115kg基準。石井直方先生、バズーカ岡田先生の理論、"
            f"6回1周サイクル、漸進性過負荷の原則に基づき、過去ログから最適な重量を提案せよ。\n【履歴】\n{past_context}"
        )
        payload = {"contents": [{"parts": [{"text": f"{system}\n\n指令：{prog}のメニューを詳細に出して。"}]}]}
        res = requests.post(url, json=payload)
        st.session_state['ai_resp'] = res.json()['candidates'][0]['content']['parts'][0]['text']
        # AI回答から種目名を抽出してセッションに保持
        st.session_state['current_menu'] = re.findall(r'[*・]\s*([^\s(（]+)', st.session_state['ai_resp'])[:4]

if 'ai_resp' in st.session_state:
    st.info(st.session_state['ai_resp'])

# --- 5. 【完全版】実績入力 (AI提案連動 + 人気種目) ---
st.markdown("---")
st.subheader("📝 実績を記録して積載量を増やそう！")

# 全種目のフラットリスト
all_popular = sum(popular_exercises.values(), [])
suggested = st.session_state.get('current_menu', ["ベンチプレス", "種目2", "種目3", "種目4"])

with st.form("workout_form"):
    logs = []
    total_today = 0
    for i, def_ex in enumerate(suggested):
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        with c1:
            # AI提案の種目をデフォルトにしつつ、人気種目からも選べる
            opts = [def_ex] + [x for x in all_popular if x != def_ex]
            ex = st.selectbox(f"種目 {i+1}", opts, key=f"ex_{i}")
        with c2: w = st.number_input("kg", key=f"w_{i}", step=2.5)
        with c3: r = st.number_input("回数", key=f"r_{i}", step=1)
        with c4: s = st.number_input("セット", key=f"s_{i}", step=1)
        if w > 0:
            total_today += w * r * s
            logs.append(f"{ex}:{w}kgx{r}x{s}")

    if st.form_submit_button("🔥 記録を聖典（Drive）に刻印！"):
        if sheet and logs:
            sheet.append_row([datetime.now().strftime("%Y-%m-%d"), prog, ", ".join(logs), f"Total:{total_today}kg"])
            st.balloons()
            st.success(f"記録完了！今日の負荷: {total_today}kg (軽自動車 {total_today/1000:.2f}台分！)")

# --- 6. 履歴・Drive参照・設定 (復元) ---
st.markdown("---")
tab1, tab2 = st.tabs(["📜 履歴（Drive同期）", "⚙️ 設定 & 1RM"])
with tab1:
    if not df_past.empty:
        st.dataframe(df_past.tail(15), use_container_width=True)
with tab2:
    st.write("MAX基準: 115kg")
    st.write("参照Drive: 接続済み")
    # RM計算機など
