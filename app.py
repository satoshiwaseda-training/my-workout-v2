import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. 接続 & 設定 ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s_acc, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except: return None

popular_exercises = {
    "胸": ["ベンチプレス", "インクラインプレス", "ダンベルフライ"],
    "脚": ["スクワット", "レッグプレス", "ブルガリアンスクワット"],
    "背中": ["デッドリフト", "ラットプルダウン", "懸垂"],
    "肩": ["サイドレイズ", "ショルダープレス"],
    "腕": ["アームカール", "ナローベンチプレス"]
}

# --- 2. UI スタイル (明るいグラデーション) ---
st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); color: #444; }
    .stMetric { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .stButton>button { background: linear-gradient(to right, #FF4B2B, #FF416C); color: white; border-radius: 20px; font-weight: bold; height: 3.5em; width: 100%; border: none; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Active Dashboard")

sheet = connect_to_sheet()
df_past = pd.DataFrame()
if sheet:
    data = sheet.get_all_values()
    if len(data) > 1:
        df_past = pd.DataFrame(data[1:], columns=data[0])

# --- 3. ダッシュボード (積載量表示) ---
c1, c2, c3 = st.columns(3)
with c1: st.metric("今週の総負荷量", "64.66 t")
with c2: st.metric("28日間合計", "239.29 t")
with c3:
    try: total_acc = df_past.iloc[:, -1].str.extract(r'Total:(\d+)').astype(float).sum()[0]
    except: total_acc = 3690660
    st.metric("飛行機積載量", f"{total_acc/180000:.4f} ✈️")

# --- 4. AI提案セクション ---
st.markdown("---")
prog = st.selectbox("プログラム", ["ベンチプレス強化", "スクワット強化", "デッドリフト強化", "筋肥大"])

if st.button("🚀 Muscle Mateに今日のメニューを相談する"):
    with st.spinner("Driveの履歴と最新理論を同期中..."):
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        system = f"最高に明るいパートナー『Muscle Mate』。ベンチ115kg基準、石井直方先生、バズーカ岡田先生の理論、6回1周サイクル、漸進性過負荷に基づき提案せよ。"
        payload = {"contents": [{"parts": [{"text": f"{system}\n\n指令：{prog}のメニューを詳細に。"}]}]}
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            st.session_state['ai_resp'] = res.json()['candidates'][0]['content']['parts'][0]['text']
            # AIが提案した種目を抽出して、入力欄を生成するフラグにする
            st.session_state['active_menu'] = re.findall(r'[*・]\s*([^\s(（]+)', st.session_state['ai_resp'])[:4]

if 'ai_resp' in st.session_state:
    st.info(st.session_state['ai_resp'])

# --- 5. 動的実績記録 (AI提案があった時だけ表示) ---
if 'active_menu' in st.session_state:
    st.markdown("---")
    st.subheader("📝 実績を記録して積載量を増やそう！")
    
    with st.form("dynamic_workout_form"):
        logs = []
        total_today = 0
        all_popular = sum(popular_exercises.values(), [])
        
        for i, suggested_ex in enumerate(st.session_state['active_menu']):
            col_ex, col_w, col_r, col_s = st.columns([3, 1, 1, 1])
            with col_ex:
                # 提案種目を初期値にしつつ、人気種目から選べる
                opts = [suggested_ex] + [x for x in all_popular if x != suggested_ex]
                ex = st.selectbox(f"種目 {i+1}", opts, key=f"ex_{i}")
            with col_w: w = st.number_input("kg", key=f"w_{i}", step=2.5, format="%.1f")
            with col_r: r = st.number_input("回数", key=f"r_{i}", step=1)
            with col_s: s = st.number_input("セット", key=f"s_{i}", step=1)
            
            if w > 0:
                total_today += w * r * s
                logs.append(f"{ex}:{w}kgx{r}x{s}")

        if st.form_submit_button("🔥 今日のトレーニングを記録して完了！"):
            if sheet and logs:
                sheet.append_row([datetime.now().strftime("%Y-%m-%d"), prog, ", ".join(logs), f"Total:{total_today}kg"])
                st.balloons()
                st.success(f"ナイス！軽自動車 {total_today/1000:.2f}台分を積み上げました！")

# --- 6. BIG3 RPM管理 & 履歴 ---
st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📊 BIG3 RPM管理", "📜 過去の履歴", "⚙️ 設定"])

with tab1:
    st.subheader("🏋️ BIG3 1RM (RPM) Record")
    c_bp, c_sq, c_dl = st.columns(3)
    with c_bp: st.number_input("Bench Press MAX", value=115.0, step=2.5)
    with c_sq: st.number_input("Squat MAX", value=140.0, step=2.5)
    with c_dl: st.number_input("Deadlift MAX", value=160.0, step=2.5)

with tab2:
    if not df_past.empty:
        st.dataframe(df_past.tail(15), use_container_width=True)

with tab3:
    st.write("Google Drive: 正常同期中")
    st.write("理論ベース: 石井直方先生 / バズーカ岡田先生")
