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
        return sheet, client
    except: return None, None

# --- 2. UI スタイル (明るいグラデーション) ---
st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); }
    .stMetric { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .stButton>button { background: linear-gradient(to right, #FF4B2B, #FF416C); color: white; border-radius: 20px; font-weight: bold; height: 3.5em; width: 100%; border: none; }
    .stNumberInput input { font-size: 1.2em !important; font-weight: bold !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Time-Critical Dashboard")

sheet, client = connect_to_google()
df_past = pd.DataFrame()
if sheet:
    data = sheet.get_all_values()
    if len(data) > 1:
        df_past = pd.DataFrame(data[1:], columns=data[0])

# --- 3. BIG3 RPM (1RM) 管理 ---
st.subheader("🏋️ BIG3 RPM (1RM) 管理")
c_bp, c_sq, c_dl = st.columns(3)
with c_bp: rpm_bp = st.number_input("Bench Press MAX", value=115.0, step=2.5)
with c_sq: rpm_sq = st.number_input("Squat MAX", value=140.0, step=2.5)
with c_dl: rpm_dl = st.number_input("Deadlift MAX", value=160.0, step=2.5)

# --- 4. 制限時間 & プログラム選択 ---
st.markdown("---")
c_time, c_prog, c_target = st.columns([1, 2, 2])
with c_time:
    t_limit = st.selectbox("トレーニング時間", [60, 90, 120], index=0, format_func=lambda x: f"{x}分")
with c_prog:
    prog = st.selectbox("プログラム", ["BIG3強化", "筋肥大", "背中・肩強化", "筋力増強"])
with c_target:
    targets = st.multiselect("対象部位", ["胸", "背中", "脚", "肩", "腕"], default=["胸"])

if st.button("🚀 制限時間内で最高のメニューを提案させる"):
    with st.spinner(f"{t_limit}分で完遂できるエビデンスベースのメニューを構築中..."):
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        system = (
            f"あなたはMuscle Mate。BP:{rpm_bp}, SQ:{rpm_sq}, DL:{rpm_dl}を基準。制限時間:{t_limit}分厳守。"
            f"セット間休憩（120秒等）を含め、時間内に収まる種目数と回数を世界中の運動生理学論文に基づき提案せよ。"
            f"説明は最小限。'種目名:重量kgx回数xセット数'の形式で箇条書きせよ。"
        )
        payload = {"contents": [{"parts": [{"text": f"{system}\n\n指令：{prog}(部位:{targets})のメニューを提示。"}]}]}
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            st.session_state['ai_resp'] = res.json()['candidates'][0]['content']['parts'][0]['text']
            # AI提案から動的に種目をパース
            parsed = []
            for line in st.session_state['ai_resp'].split('\n'):
                match = re.search(r'[*・]\s*([^:]+):(\d+\.?\d*)kgx(\d+)x(\d+)', line)
                if match:
                    parsed.append({"name": match.group(1), "w": float(match.group(2)), "r": int(match.group(3)), "s": int(match.group(4))})
            st.session_state['active_tasks'] = parsed

if 'ai_resp' in st.session_state:
    st.info(f"⏱️ {t_limit}分集中メニュー:\n{st.session_state['ai_resp']}")

# --- 5. 【完全復活】提案連動・動的入力フォーム ---
if 'active_tasks' in st.session_state and st.session_state['active_tasks']:
    st.markdown("---")
    st.subheader(f"📝 本日の実績記録 ({t_limit}min session)")
    
    with st.form("workout_sync_form"):
        current_logs = []
        total_weight = 0
        for i, item in enumerate(st.session_state['active_tasks']):
            # 基準となるMAXを表示
            ref_max = rpm_bp if "ベンチ" in item['name'] else (rpm_sq if "スクワット" in item['name'] else rpm_dl)
            
            st.markdown(f"**種目 {i+1}: {item['name']}** (MAX: {ref_max}kg)")
            c_w, c_r, c_s = st.columns(3)
            with c_w: w = st.number_input(f"重量 {i+1}", value=item['w'], key=f"w_{i}", step=2.5)
            with c_r: r = st.number_input(f"回数 {i+1}", value=item['r'], key=f"r_{i}", step=1)
            with c_s: s = st.number_input(f"セット {i+1}", value=item['s'], key=f"s_{i}", step=1)
            
            if w > 0:
                total_weight += w * r * s
                current_logs.append(f"{item['name']}:{w}kgx{r}x{s}")

        if st.form_submit_button("🔥 実績をGoogle Driveに同期して完了"):
            if sheet and current_logs:
                now = datetime.now().strftime("%Y-%m-%d")
                sheet.append_row([now, f"{prog}({t_limit}分)", ", ".join(targets), ", ".join(current_logs), f"Total:{total_weight}kg"])
                st.balloons()
                st.success(f"ナイス！総負荷 {total_weight}kg を保存しました！")

# --- 6. 履歴 ---
st.markdown("---")
st.subheader("📜 履歴（Drive同期済み）")
if not df_past.empty: st.dataframe(df_past.tail(10), use_container_width=True)
