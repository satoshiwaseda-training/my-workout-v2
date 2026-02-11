import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. UI スタイル (鉄壁の動的UI) ---
st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #ffedbc 0%, #ff9a9e 100%); }
    .stNumberInput input { font-size: 1.1em !important; font-weight: bold !important; border: 2px solid #ff4b2b !important; }
    .stButton>button { background: linear-gradient(to right, #FF4B2B, #FF416C); color: white; border-radius: 20px; font-weight: bold; height: 3.5em; width: 100%; border: none; }
    .workout-card { background: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 15px; border-left: 10px solid #FF4B2B; margin-bottom: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: The Final Precision")

# --- 2. セッション変数の初期化 (これが重要：アプリの冒頭で箱を作る) ---
if 'active_tasks' not in st.session_state:
    st.session_state['active_tasks'] = None
if 'ai_resp_text' not in st.session_state:
    st.session_state['ai_resp_text'] = ""

# --- 3. Google Sheets 接続 ---
def connect_to_google():
    try:
        s_acc = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s_acc, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except: return None

sheet = connect_to_google()

# --- 4. 1RM基準値 ---
c1, c2, c3 = st.columns(3)
with c1: rpm_bp = st.number_input("BP MAX", value=115.0, key="rpm_bp")
with c2: rpm_sq = st.number_input("SQ MAX", value=140.0, key="rpm_sq")
with c3: rpm_dl = st.number_input("DL MAX", value=160.0, key="rpm_dl")

# --- 5. 実行設定 ---
st.markdown("---")
c_time, c_target = st.columns([1, 2])
with c_time: t_limit = st.selectbox("時間", [60, 90], index=0, format_func=lambda x: f"{x}分")
with c_target: targets = st.multiselect("対象部位", ["胸 (BP)", "脚 (SQ)", "背中 (DL)", "肩", "腕"], default=["胸 (BP)"])

# --- 6. メニュー生成 (1クリックで確実に箱へ保存) ---
if st.button("🚀 最新エビデンスに基づきメニューを生成"):
    with st.spinner("AIが現実的な強度を算出中..."):
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        system = (
            f"あなたはMuscle Mate。BP:{rpm_bp}kg基準。時間{t_limit}分。休憩(180秒/90秒)を計算に含め、種目数を3種目に厳選。"
            f"重量は一般的で安全なRPE8を基準。1RMの60-75%程度で算出。"
            f"出力形式：'種目名:重量kgx回数xセット数[休憩:秒]'"
        )
        payload = {"contents": [{"parts": [{"text": f"{system}\n\n指令：本日の設計図を出せ。"}]}]}
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            resp_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            st.session_state['ai_resp_text'] = resp_text
            
            parsed = []
            for line in resp_text.split('\n'):
                match = re.search(r'[*・]?\s*([^:]+):(\d+\.?\d*)kgx(\d+)x(\d+)\[休憩:(\d+)\]', line)
                if match:
                    parsed.append({"name": match.group(1), "w": float(match.group(2)), "r": int(match.group(3)), "s": int(match.group(4)), "rest": int(match.group(5))})
            
            # 記憶の箱に保存して、画面を更新
            st.session_state['active_tasks'] = parsed
            st.rerun()

# --- 7. 【死守UI】記録欄の表示 (箱にデータがある限り、絶対に出す) ---
if st.session_state['active_tasks']:
    st.info(f"📋 推奨プラン:\n{st.session_state['ai_resp_text']}")
    
    with st.form("ultimate_record_form"):
        all_logs = []
        total_vol = 0
        for i, task in enumerate(st.session_state['active_tasks']):
            st.markdown(f'<div class="workout-card">### 🏋️ {task["name"]} (休憩: {task["rest"]}s)</div>', unsafe_allow_html=True)
            for s_num in range(1, task['s'] + 1):
                col_label, col_w, col_r = st.columns([1, 2, 2])
                with col_label: st.write(f"Set {s_num}")
                # keyに一意性を持たせることで、Streamlitが値を正しく管理
                w = st.number_input(f"重量(kg)", value=task['w'], key=f"inp_w_{i}_{s_num}", step=0.5)
                r = st.number_input(f"回数", value=task['r'], key=f"inp_r_{i}_{s_num}", step=1)
                
                if w > 0:
                    total_vol += w * r
                    all_logs.append(f"{task['name']}(S{s_num}):{w}kgx{r}")
            st.markdown("---")

        if st.form_submit_button("🔥 実績をGoogle Driveへ保存"):
            if sheet and all_logs:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                sheet.append_row([now, f"{t_limit}min session", ", ".join(targets), ", ".join(all_logs), f"Vol:{total_vol}kg"])
                st.balloons()
                st.success(f"完璧ですサトシさん！総負荷 {total_vol}kg を保存しました！")
                st.session_state['active_tasks'] = None # 保存後にリセット
