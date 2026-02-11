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
    .workout-card { background: rgba(255, 255, 255, 0.7); padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #ff9a9e; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Absolute Sync Dashboard")

sheet = connect_to_google()
df_past = pd.DataFrame()
if sheet:
    data = sheet.get_all_values()
    if len(data) > 1: df_past = pd.DataFrame(data[1:], columns=data[0])

# --- 3. BIG3 RPM (1RM) 管理 ---
st.subheader("🏋️ BIG3 1RM基準値（現在の限界）")
c_bp, c_sq, c_dl = st.columns(3)
with c_bp: rpm_bp = st.number_input("Bench Press MAX", value=115.0, step=2.5, key="rpm_bp")
with c_sq: rpm_sq = st.number_input("Squat MAX", value=140.0, step=2.5, key="rpm_sq")
with c_dl: rpm_dl = st.number_input("Deadlift MAX", value=160.0, step=2.5, key="rpm_dl")

# --- 4. 時間・部位・プログラム選択 ---
st.markdown("---")
col_time, col_prog, col_target = st.columns([1, 2, 2])
with col_time: t_limit = st.selectbox("トレーニング時間", [60, 90], index=0, format_func=lambda x: f"{x}分")
with col_prog: prog = st.selectbox("プログラム", ["BIG3強化", "背中・肩特化", "筋力増強", "筋肥大"])
with col_target: targets = st.multiselect("対象部位", ["胸", "背中", "脚", "肩", "腕"], default=["胸", "腕"])

# --- 5. AIメニュー生成 ---
if st.button("🚀 最新のエビデンスに基づきメニューを生成"):
    with st.spinner("世界中の論文データをスキャンし、最適メニューを算出中..."):
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        system = (
            f"あなたは最高のパートナー『Muscle Mate』。BP:{rpm_bp}, SQ:{rpm_sq}, DL:{rpm_dl}kgを100%基準。時間{t_limit}分。"
            f"部位:{targets}に特化し、それ以外の種目は絶対に出すな。"
            f"世界中の最新スポーツ科学論文に基づき、解説抜きで'種目名:重量kgx回数xセット数'の形式のみで出せ。"
        )
        payload = {"contents": [{"parts": [{"text": f"{system}\n\n指令：{prog}の今日のメニューを提案して。"}]}]}
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            resp_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            st.session_state['ai_resp'] = resp_text
            # 種目をパース
            parsed = []
            for line in resp_text.split('\n'):
                match = re.search(r'[*・]\s*([^:]+):(\d+\.?\d*)kgx(\d+)x(\d+)', line)
                if match:
                    parsed.append({"name": match.group(1), "w": float(match.group(2)), "r": int(match.group(3)), "s": int(match.group(4))})
            st.session_state['active_tasks'] = parsed

# --- 6. 【修正：絶対に消えない】AI提案連動・セット別入力欄 ---
if 'ai_resp' in st.session_state:
    st.info(f"📋 推奨プラン ({t_limit}分):\n{st.session_state['ai_resp']}")
    
    if 'active_tasks' in st.session_state and st.session_state['active_tasks']:
        st.markdown("---")
        st.subheader(f"📝 本日の実績記録 ({', '.join(targets)})")
        
        with st.form("ultimate_workout_form"):
            all_logs = []
            total_vol = 0
            
            for i, task in enumerate(st.session_state['active_tasks']):
                st.markdown(f"#### 🏋️ {task['name']} (推奨: {task['w']}kg)")
                
                # セット数分、確実に行を生成
                for s_num in range(1, task['s'] + 1):
                    c_label, c_w, c_r = st.columns([1, 2, 2])
                    with c_label: st.write(f"Set {s_num}")
                    with c_w: w = st.number_input(f"重量 (kg)", value=task['w'], key=f"w_{i}_{s_num}", step=2.5)
                    with c_r: r = st.number_input(f"回数", value=task['r'], key=f_r_{i}_{s_num}, step=1)
                    
                    if w > 0:
                        total_vol += w * r
                        all_logs.append(f"{task['name']}(S{s_num}):{w}kgx{r}")
                st.markdown("<hr style='border: 1px dashed #ff9a9e'>", unsafe_allow_html=True)

            if st.form_submit_button("🔥 すべての実績をDriveへ同期して完了！"):
                if sheet and all_logs:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    sheet.append_row([now, f"{prog}({t_limit}分)", ", ".join(targets), ", ".join(all_logs), f"Total:{total_vol}kg"])
                    st.balloons()
                    st.success(f"完璧です！総負荷量 {total_vol}kg (飛行機 {total_vol/180000:.4f}機分) を保存しました！")
                    # セッション情報をクリア
                    for key in st.session_state.keys():
                        if key.startswith(('w_', 'r_')): del st.session_state[key]

# --- 7. 履歴 ---
st.markdown("---")
st.subheader("📜 トレーニング履歴 (Drive同期)")
if not df_past.empty: st.dataframe(df_past.tail(15), use_container_width=True)
