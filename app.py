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

# --- 2. UI スタイル (モチベ最大化グラデーション) ---
st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); }
    .stMetric { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .stButton>button { background: linear-gradient(to right, #FF4B2B, #FF416C); color: white; border-radius: 20px; font-weight: bold; height: 3.5em; width: 100%; border: none; }
    .stNumberInput input { font-size: 1.1em !important; font-weight: bold !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Active Dashboard")

sheet, client = connect_to_google()
df_past = pd.DataFrame()
if sheet:
    data = sheet.get_all_values()
    if len(data) > 1:
        df_past = pd.DataFrame(data[1:], columns=data[0])

# --- 3. BIG3 RPM (1RM) 入力欄 ---
st.subheader("🏋️ BIG3 RPM (1RM) 管理")
c_bp, c_sq, c_dl = st.columns(3)
with c_bp: rpm_bp = st.number_input("Bench Press MAX", value=115.0, step=2.5)
with c_sq: rpm_sq = st.number_input("Squat MAX", value=140.0, step=2.5)
with c_dl: rpm_dl = st.number_input("Deadlift MAX", value=160.0, step=2.5)

# --- 4. プログラム・部位選択 & AI提案 ---
st.markdown("---")
col_p, col_t = st.columns(2)
with col_p:
    prog = st.selectbox("プログラム", ["BIG3強化", "背中強化", "肩強化", "筋力増強"])
with col_t:
    targets = st.multiselect("対象部位", ["胸", "背中", "脚", "肩", "腕"], default=["胸"])

if st.button("🚀 今日の最適メニューを算出（世界中の論文ベース）"):
    with st.spinner("最新エビデンスを同期中..."):
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        system = (
            f"あなたはMuscle Mate。BP:{rpm_bp}, SQ:{rpm_sq}, DL:{rpm_dl}を100%とし、最新のスポーツ科学に基づきメニューを出せ。"
            f"説明は不要。'種目名:重量kgx回数xセット数'の形式で簡潔に箇条書きせよ。"
        )
        payload = {"contents": [{"parts": [{"text": f"{system}\n\n指令：{prog}(部位:{targets})のメニューを提示。"}]}]}
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            st.session_state['ai_resp'] = res.json()['candidates'][0]['content']['parts'][0]['text']
            # AI提案から種目・重量・回数をパースしてリスト化
            parsed_menu = []
            lines = st.session_state['ai_resp'].split('\n')
            for line in lines:
                match = re.search(r'[*・]\s*([^:]+):(\d+\.?\d*)kgx(\d+)x(\d+)', line)
                if match:
                    parsed_menu.append({
                        "name": match.group(1),
                        "w": float(match.group(2)),
                        "r": int(match.group(3)),
                        "s": int(match.group(4))
                    })
            st.session_state['active_tasks'] = parsed_menu

if 'ai_resp' in st.session_state:
    st.markdown("### 📋 AI提案メニュー")
    st.code(st.session_state['ai_resp'])

# --- 5. 【復元】提案と100%連動した入力フォーム ---
if 'active_tasks' in st.session_state:
    st.markdown("---")
    st.subheader(f"📝 本日の調練記録 ({', '.join(targets)})")
    
    with st.form("workout_sync_form"):
        current_logs = []
        total_weight = 0
        for i, item in enumerate(st.session_state['active_tasks']):
            # 過去のMAX（RPM）を動的に参照
            past_max = rpm_bp if "ベンチ" in item['name'] else (rpm_sq if "スクワット" in item['name'] else rpm_dl)
            
            st.markdown(f"**種目 {i+1}: {item['name']}** (推奨: {item['w']}kg / MAX: {past_max}kg)")
            c_w, c_r, c_s = st.columns(3)
            with c_w: w = st.number_input("重量 (kg)", value=item['w'], key=f"w_{i}", step=2.5)
            with c_r: r = st.number_input("レップ数", value=item['r'], key=f"r_{i}", step=1)
            with c_s: s = st.number_input("セット数", value=item['s'], key=f"s_{i}", step=1)
            
            if w > 0:
                total_weight += w * r * s
                current_logs.append(f"{item['name']}:{w}kgx{r}x{s}")

        if st.form_submit_button("🔥 実績をDriveに同期して完了"):
            if sheet and current_logs:
                now = datetime.now().strftime("%Y-%m-%d")
                sheet.append_row([now, prog, ", ".join(targets), ", ".join(current_logs), f"Total:{total_weight}kg"])
                st.balloons()
                st.success(f"ナイス！総負荷 {total_weight}kg (飛行機 {total_weight/180000:.4f}機分) を保存しました！")

# --- 6. 履歴 ---
st.markdown("---")
st.subheader("📜 過去の履歴 (Google Drive同期)")
if not df_past.empty:
    st.dataframe(df_past.tail(15), use_container_width=True)
