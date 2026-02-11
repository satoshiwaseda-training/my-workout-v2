import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. 初期化 (Session State で種目リストを管理) ---
if 'active_tasks' not in st.session_state:
    st.session_state.active_tasks = []

st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #ffedbc 0%, #ff9a9e 100%); }
    .stNumberInput input { font-size: 1.1em !important; font-weight: bold !important; border: 2px solid #ff4b2b !important; }
    .stButton>button { background: linear-gradient(to right, #FF4B2B, #FF416C); color: white; border-radius: 20px; font-weight: bold; height: 3.5em; width: 100%; border: none; }
    .workout-card { background: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 15px; border-left: 10px solid #FF4B2B; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Universal Session Tracker")

# --- 2. Google Sheets 接続 ---
def connect_to_google():
    try:
        s_acc = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s_acc, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except: return None

sheet = connect_to_google()

# --- 3. 1RM基準値 & 基本設定 ---
c1, c2, c3 = st.columns(3)
with c1: rpm_bp = st.number_input("BP MAX", value=115.0, key="rpm_bp")
with c2: rpm_sq = st.number_input("SQ MAX", value=140.0, key="rpm_sq")
with c3: rpm_dl = st.number_input("DL MAX", value=160.0, key="rpm_dl")

st.markdown("---")
c_time, c_target = st.columns([1, 2])
with c_time: t_limit = st.selectbox("時間", [60, 90], index=0)
with c_target: targets = st.multiselect("対象部位", ["胸 (BP)", "脚 (SQ)", "背中 (DL)", "肩", "腕"], default=["胸 (BP)"])

# --- 4. メニュー生成ロジック (AI提案) ---
if st.button("🚀 AIに設計図を依頼する"):
    with st.spinner("AIが提案を作成中..."):
        try:
            api_key = st.secrets["GOOGLE_API_KEY"].strip()
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
            system = (f"Muscle MateとしてBP:{rpm_bp}kg基準で{t_limit}分、{targets}のメニューを提案せよ。"
                      "形式：種目名:重量kgx回数xセット数[休憩:秒]")
            payload = {"contents": [{"parts": [{"text": system}]}]}
            res = requests.post(url, json=payload, timeout=15)
            if res.status_code == 200:
                resp_text = res.json()['candidates'][0]['content']['parts'][0]['text']
                parsed = []
                for line in resp_text.split('\n'):
                    match = re.search(r'([^:：]+)[:：]\s*(\d+\.?\d*)\s*kg?\s*x\s*(\d+)\s*x\s*(\d+)', line, re.IGNORECASE)
                    if match:
                        parsed.append({"name": match.group(1).strip("*・ "), "w": float(match.group(2)), "r": int(match.group(3)), "s": int(match.group(4))})
                st.session_state.active_tasks = parsed
                st.rerun()
        except: st.error("通信失敗。手動で追加してください。")

# --- 5. 手動追加機能 ---
if st.button("➕ 種目を手動で追加"):
    st.session_state.active_tasks.append({"name": "新規種目", "w": 0.0, "r": 0, "s": 3})
    st.rerun()

# --- 6. 【最重要UI】動的入力フォーム ---
if st.session_state.active_tasks:
    with st.form("dynamic_workout_form"):
        all_logs = []
        total_vol = 0
        for i, task in enumerate(st.session_state.active_tasks):
            st.markdown(f'<div class="workout-card">', unsafe_allow_html=True)
            t_name = st.text_input(f"種目名 {i+1}", value=task['name'], key=f"name_{i}")
            t_sets = st.number_input(f"セット数", value=task['s'], key=f"sets_{i}", min_value=1, max_value=10)
            
            for s_num in range(1, t_sets + 1):
                col1, col2 = st.columns(2)
                with col1: w = st.number_input(f"S{s_num} 重量(kg)", value=task.get('w', 0.0), key=f"w_{i}_{s_num}", step=0.5)
                with col2: r = st.number_input(f"S{s_num} 回数", value=float(task.get('r', 0)), key=f"r_{i}_{s_num}", step=1.0)
                if w > 0 or r > 0:
                    total_vol += w * r
                    all_logs.append(f"{t_name}(S{s_num}):{w}kgx{int(r)}")
            st.markdown('</div>', unsafe_allow_html=True)

        c_save, c_clear = st.columns(2)
        with c_save:
            if st.form_submit_button("🔥 実績をGoogle Driveへ保存"):
                if sheet and all_logs:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    sheet.append_row([now, f"{t_limit}min", ", ".join(targets), ", ".join(all_logs), f"{total_vol}kg"])
                    st.balloons()
                    st.session_state.active_tasks = []
                    st.rerun()
        with c_clear:
            if st.form_submit_button("🗑️ メニューをクリア"):
                st.session_state.active_tasks = []
                st.rerun()
