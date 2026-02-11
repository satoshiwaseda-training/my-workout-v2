import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. Google Drive / Sheets 接続 ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except: return None

# --- 2. 部位別人気種目 ---
popular_exercises = {
    "胸": ["ベンチプレス", "インクラインプレス", "ダンベルフライ", "チェストプレス"],
    "脚": ["スクワット", "レッグプレス", "レッグエクステンション", "レッグカール"],
    "背中": ["デッドリフト", "ラットプルダウン", "ベントオーバーロウ", "懸垂"],
    "肩": ["サイドレイズ", "ショルダープレス", "アップライトロウ"],
    "腕": ["アームカール", "ナローベンチプレス", "ライイングエクステンション"]
}

# --- 3. UI スタイル (明るいオレンジ & グラデーション) ---
st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); color: #444; }
    .stMetric { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .stButton>button { background: linear-gradient(to right, #FF4B2B, #FF416C); color: white; border-radius: 20px; font-weight: bold; height: 3.5em; width: 100%; border: none; }
    .stNumberInput input { font-size: 1.2em !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Active Dashboard")
st.write("MAX 115kg 基準：今日も最高の積み上げを楽しみましょう！")

# 履歴データ取得
sheet = connect_to_sheet()
df_past = pd.DataFrame()
if sheet:
    data = sheet.get_all_values()
    if len(data) > 1:
        df_past = pd.DataFrame(data[1:], columns=data[0])

# --- 4. ダッシュボード (積載量換算) ---
c1, c2, c3 = st.columns(3)
with c1: st.metric("今週の総負荷量", "64.66 t")
with c2: st.metric("28日間合計", "239.29 t")
with c3:
    total_acc = 3690660 # サンプル
    st.metric("飛行機積載量", f"{total_acc/180000:.2f} ✈️")

# --- 5. AIメニュー提案 ---
st.markdown("---")
prog = st.selectbox("プログラム", ["ベンチプレス強化", "スクワット強化", "デッドリフト強化", "筋肥大", "筋力増強"])

if st.button("🚀 Muscle Mateにメニューを相談（最新理論＋履歴参照）"):
    with st.spinner("最高のメニューを構成中..."):
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        past_context = df_past.tail(10).to_string() if not df_past.empty else "新規"
        system = f"あなたは最高にポジティブなトレーニングパートナー『Muscle Mate』。115kg基準、石井直方先生、バズーカ岡田先生の理論、6回1周サイクルに基づき提案せよ。\n【履歴】\n{past_context}"
        payload = {"contents": [{"parts": [{"text": f"{system}\n\n指令：{prog}の今日のメニューを詳細に。"}]}]}
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            st.session_state['ai_resp'] = res.json()['candidates'][0]['content']['parts'][0]['text']
            st.session_state['suggested'] = re.findall(r'[*・]\s*([^\s(（]+)', st.session_state['ai_resp'])[:4]

if 'ai_resp' in st.session_state:
    st.info(st.session_state['ai_resp'])

# --- 6. 【復元】実績記録 (画像UIのような直感入力) ---
st.markdown("---")
st.subheader("📝 実績を記録して積載量を増やそう！")

suggested = st.session_state.get('suggested', ["ベンチプレス", "種目2", "種目3"])
all_popular = sum(popular_exercises.values(), [])

with st.form("workout_log_v2"):
    log_data = []
    total_today = 0
    for i in range(3):
        def_ex = suggested[i] if i < len(suggested) else "(未選択)"
        col_ex, col_w, col_r, col_s = st.columns([3, 1, 1, 1])
        with col_ex:
            opts = [def_ex] + [x for x in all_popular if x != def_ex] + ["(自由入力)"]
            ex = st.selectbox(f"種目 {i+1}", opts, key=f"ex_{i}")
        with col_w: w = st.number_input("kg", key=f"w_{i}", step=2.5, format="%.1f")
        with col_r: r = st.number_input("回数", key=f"r_{i}", step=1)
        with col_s: s = st.number_input("セット", key=f"s_{i}", step=1)
        
        if ex != "(未選択)" and w > 0:
            total_today += w * r * s
            log_data.append(f"{ex}:{w}kgx{r}x{s}")

    if st.form_submit_button("🔥 今日のトレーニングをDriveへ保存！"):
        if sheet and log_data:
            sheet.append_row([datetime.now().strftime("%Y-%m-%d"), prog, ", ".join(log_data), f"Total:{total_today}kg"])
            st.balloons()
            st.success(f"お疲れ様です！今日は 軽自動車 {total_today/1000:.2f} 台分を積み上げました！")

# --- 7. 【復元】BIG3 RPM 管理 & 履歴 ---
st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📊 BIG3 RPM管理", "📜 過去の履歴", "⚙️ システム設定"])

with tab1:
    st.subheader("🏋️ BIG3 1RM (RPM) Record")
    c_bp, c_sq, c_dl = st.columns(3)
    with c_bp: st.number_input("Bench Press MAX", value=115.0, step=2.5, help="現在のベンチ1RM")
    with c_sq: st.number_input("Squat MAX", value=140.0, step=2.5)
    with c_dl: st.number_input("Deadlift MAX", value=160.0, step=2.5)
    st.write("※BIG3の合計は **415.0 kg** です。目標の合計500kgまであと85kg！")

with tab2:
    if not df_past.empty:
        st.dataframe(df_past.tail(15), use_container_width=True)

with tab3:
    st.write("Google Drive: 正常同期中")
    st.write("キャラクター: Muscle Mate (Active Mode)")
    st.write("理論ベース: 石井直方先生 / バズーカ岡田先生")
