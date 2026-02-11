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
        return client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except: return None

# --- 2. UI スタイル (モチベ最大化グラデーション) ---
st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #FF9A9E 0%, #FAD0C4 100%); }
    .stMetric { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .stButton>button { background: linear-gradient(to right, #FF4B2B, #FF416C); color: white; border-radius: 20px; font-weight: bold; height: 3.5em; width: 100%; border: none; font-size: 1.1em; }
    .stNumberInput input { font-size: 1.1em !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Total Body Dashboard")

# 接続 & 履歴取得
sheet = connect_to_google()
df_past = pd.DataFrame()
if sheet:
    data = sheet.get_all_values()
    if len(data) > 1:
        df_past = pd.DataFrame(data[1:], columns=data[0])

# --- 3. BIG3 RPM (1RM) 管理 ---
st.subheader("🏋️ BIG3 & 部位別 RPM 管理")
c_bp, c_sq, c_dl = st.columns(3)
with c_bp: rpm_bp = st.number_input("Bench Press MAX (kg)", value=115.0, step=2.5, key="rpm_bp")
with c_sq: rpm_sq = st.number_input("Squat MAX (kg)", value=140.0, step=2.5, key="rpm_sq")
with c_dl: rpm_dl = st.number_input("Deadlift MAX (kg)", value=160.0, step=2.5, key="rpm_dl")

# --- 4. プログラム & 部位選択 (背中・肩を完全復活) ---
st.markdown("---")
col_p, col_t = st.columns(2)
with col_p:
    prog = st.selectbox("プログラム", 
                        ["BIG3強化", "背中強化(広背筋・僧帽筋)", "肩強化(三角筋)", "筋肥大モード", "筋力増強"])
with col_t:
    targets = st.multiselect("対象部位", ["胸", "背中", "脚", "肩", "腕", "腹筋"], 
                            default=["背中"] if "背中" in prog else (["肩"] if "肩" in prog else ["胸"]))

if st.button("🚀 今日の最適メニューを世界中の論文から算出"):
    with st.spinner("最新のエビデンスと過去ログを同期中..."):
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        past_context = df_past.tail(10).to_string() if not df_past.empty else "初回"
        # 科学的根拠を世界規模に拡張し、各部位への特化を命令
        system = (
            f"あなたは最高のパートナー『Muscle Mate』。以下の数値を100%基準とする。\n"
            f"BP:{rpm_bp}kg, SQ:{rpm_sq}kg, DL:{rpm_dl}kg。\n"
            f"世界の最新スポーツ科学論文に基づき、{prog}に最適な種目を提案せよ。特に部位:{targets}の筋肥大と筋力向上の両立を目指せ。"
        )
        payload = {"contents": [{"parts": [{"text": f"{system}\n\n指令：今日の具体的メニューを出して。"}]}]}
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            st.session_state['ai_resp'] = res.json()['candidates'][0]['content']['parts'][0]['text']
            # AIが提案した種目を抽出（正規表現でリスト化）
            st.session_state['active_tasks'] = re.findall(r'[*・]\s*([^\s(（]+)', st.session_state['ai_resp'])[:5]

if 'ai_resp' in st.session_state:
    st.info(st.session_state['ai_resp'])

# --- 5. 動的実績記録 (AI提案種目のみ表示) ---
if 'active_tasks' in st.session_state:
    st.markdown("---")
    st.subheader(f"📝 本日の調練実績 ({', '.join(targets)})")
    with st.form("workout_log_final"):
        logs = []
        total_today = 0
        for i, task in enumerate(st.session_state['active_tasks']):
            c_ex, c_w, c_r, c_s = st.columns([3, 1, 1, 1])
            with c_ex: ex = st.text_input(f"種目 {i+1}", value=task, key=f"ex_{i}")
            with c_w: w = st.number_input("kg", key=f"w_{i}", step=2.5, format="%.1f")
            with c_r: r = st.number_input("回数", key=f"r_{i}", step=1)
            with c_s: s = st.number_input("セット", key=f"s_{i}", step=1)
            
            if w > 0:
                total_today += w * r * s
                logs.append(f"{ex}:{w}kgx{r}x{s}")

        if st.form_submit_button("🔥 記録を保存 (Drive同期)"):
            if sheet and logs:
                now = datetime.now().strftime("%Y-%m-%d")
                sheet.append_row([now, prog, ", ".join(targets), ", ".join(logs), f"Total:{total_today}kg"])
                st.balloons()
                st.success(f"完了！今日の積載量は {total_today}kg (飛行機換算 {total_today/180000:.4f}機分) です！")

# --- 6. 履歴 & 設定 ---
st.markdown("---")
tab1, tab2 = st.tabs(["📜 履歴（Drive同期）", "⚙️ 設定"])
with tab1:
    if not df_past.empty: st.dataframe(df_past.tail(15), use_container_width=True)
with tab2:
    st.write(f"BIG3 Total RPM: {rpm_bp + rpm_sq + rpm_dl} kg")
    st.write("科学的根拠: 全世界のスポーツ科学論文 / 連携: Google Drive")
