import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. Google 連携 (Drive & Sheets) ---
def connect_to_google():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
        return sheet
    except: return None

# --- 2. UI スタイル (明るいグラデーション) ---
st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #ffedbc 0%, #ff9a9e 100%); color: #444; }
    .stNumberInput input { font-size: 1.1em !important; font-weight: bold !important; border-radius: 8px !important; }
    .stButton>button { background: linear-gradient(to right, #FF4B2B, #FF416C); color: white; border-radius: 20px; font-weight: bold; height: 3.5em; width: 100%; border: none; }
    .stInfo { background-color: rgba(255, 255, 255, 0.7); border: none; color: #333; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Real-time Analyst")

sheet = connect_to_google()
df_past = pd.DataFrame()
if sheet:
    data = sheet.get_all_values()
    if len(data) > 1: df_past = pd.DataFrame(data[1:], columns=data[0])

# --- 3. BIG3 1RM基準値 ---
st.subheader("🏋️ BIG3 1RM基準")
c_bp, c_sq, c_dl = st.columns(3)
with c_bp: rpm_bp = st.number_input("Bench Press MAX", value=115.0, step=2.5, key="rpm_bp")
with c_sq: rpm_sq = st.number_input("Squat MAX", value=140.0, step=2.5, key="rpm_sq")
with c_dl: rpm_dl = st.number_input("Deadlift MAX", value=160.0, step=2.5, key="rpm_dl")

# --- 4. メニュー生成セクション ---
st.markdown("---")
col_time, col_prog, col_target = st.columns([1, 2, 2])
with col_time: t_limit = st.selectbox("時間", [60, 90], index=0, format_func=lambda x: f"{x}分")
with col_prog: prog = st.selectbox("プログラム", ["BIG3強化", "筋肥大", "背中・肩特化", "筋力増強"])
with col_target: targets = st.multiselect("部位", ["胸", "背中", "脚", "肩", "腕"], default=["胸", "腕"])

if st.button("🚀 最新エビデンスに基づきメニューを生成"):
    with st.spinner("世界中の論文データを解析中..."):
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        system = (
            f"あなたは最高のパートナー『Muscle Mate』。BP:{rpm_bp}, SQ:{rpm_sq}, DL:{rpm_dl}kgを100%基準とする。"
            f"世界の最新スポーツ科学（Prilepin表等）に基づき、{t_limit}分で終わるメニューを出せ。"
            f"解説禁止。'種目名:重量kgx回数xセット数'の形式のみ厳守。重量は1RMの60-85%で算出せよ。"
        )
        payload = {"contents": [{"parts": [{"text": f"{system}\n\n指令：{prog}(部位:{targets})のメニュー提示。"}]}]}
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            resp_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            st.session_state['ai_resp'] = resp_text
            
            # 種目をパースしてセッションに保存
            parsed = []
            for line in resp_text.split('\n'):
                match = re.search(r'[*・]\s*([^:]+):(\d+\.?\d*)kgx(\d+)x(\d+)', line)
                if match:
                    parsed.append({"name": match.group(1), "w": float(match.group(2)), "r": int(match.group(3)), "s": int(match.group(4))})
            st.session_state['active_tasks'] = parsed

# --- 5. 【完全復活】AI提案と完全連動したセット別入力欄 ---
if 'ai_resp' in st.session_state:
    st.info(f"⏱️ {t_limit}分集中メニュー:\n{st.session_state['ai_resp']}")
    
    if 'active_tasks' in st.session_state:
        st.markdown("---")
        st.subheader("📝 本日の実績記録（セット別）")
        
        with st.form("workout_input_form"):
            all_logs = []
            total_vol = 0
            
            for i, task in enumerate(st.session_state['active_tasks']):
                st.markdown(f"#### 【{task['name']}】 (推奨: {task['w']}kg)")
                
                # セット数分、確実にループして入力欄を生成
                for s_num in range(1, task['s'] + 1):
                    c_label, c_w, c_r = st.columns([1, 2, 2])
                    with c_label: st.write(f"Set {s_num}")
                    with c_w: w = st.number_input(f"重量 (kg)", value=task['w'], key=f"w_{i}_{s_num}", step=2.5)
                    with c_r: r = st.number_input(f"回数", value=task['r'], key=f"r_{i}_{s_num}", step=1)
                    
                    if w > 0:
                        total_vol += w * r
                        all_logs.append(f"{task['name']}(S{s_num}):{w}kgx{r}")
                st.markdown("---")

            if st.form_submit_button("🔥 今日の全セットを記録してDriveに保存！"):
                if sheet and all_logs:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    sheet.append_row([now, f"{prog}({t_limit}分)", ", ".join(targets), ", ".join(all_logs), f"Total:{total_vol}kg"])
                    st.balloons()
                    st.success(f"お疲れ様でした！総負荷 {total_vol}kg を保存しました！")
                    # 保存後はリセット
                    for key in st.session_state.keys():
                        if key.startswith(('w_', 'r_')): del st.session_state[key]

# --- 6. 履歴 ---
st.markdown("---")
st.subheader("📜 履歴")
if not df_past.empty: st.dataframe(df_past.tail(15), use_container_width=True)
