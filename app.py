import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. 聖域接続 (Sheets & Drive) ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except: return None

# --- 2. 換算・コレクションロジック ---
def render_muscle_sidebar(total_accumulated_weight):
    st.sidebar.markdown(f"""
        <div style='background: linear-gradient(to bottom, #FF8C00, #FF4500); padding: 20px; border-radius: 15px; color: white; text-align: center;'>
            <h2 style='margin:0;'>🏆 Muscle Collection</h2>
            <p style='font-size: 0.8em;'>累計負荷: {total_accumulated_weight/1000:.2f} t</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    achievements = [
        (1000, "軽自動車", "🚗"), (5000, "アフリカゾウ", "🐘"), 
        (12000, "大型バス", "🚌"), (180000, "ジャンボジェット", "✈️"),
        (36000000, "スカイツリー", "🗼")
    ]
    
    for threshold, name, icon in achievements:
        if total_accumulated_weight >= threshold:
            st.sidebar.success(f"{icon} {name} 解放済み！")
        else:
            prog = min((total_accumulated_weight / threshold), 1.0)
            st.sidebar.write(f"🔒 {name} (残り {(threshold - total_accumulated_weight)/1000:.1f}t)")
            st.sidebar.progress(prog)

# --- 3. UI 構築 (115kg 基準版) ---
st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")

st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #fdfcfb 0%, #e2d1c3 100%); color: #333; }
    .stMetric { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .stButton>button { background: linear-gradient(45deg, #FF512F 0%, #DD2476 100%); color: white; border-radius: 30px; border: none; font-weight: bold; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Bench Press 115kg Edition")
st.write("MAX 115kg突破おめでとうございます！新たな高みへ、科学の力で挑みましょう！")

# 過去データ取得
sheet = connect_to_sheet()
all_data = sheet.get_all_values() if sheet else []
df_past = pd.DataFrame(all_data[1:], columns=all_data[0]) if len(all_data) > 1 else pd.DataFrame()

# サイドバー図鑑表示
# 累積重量計算（スプレッドシートの最後の列から数値を抽出）
try:
    total_w = df_past.iloc[:, -1].str.extract(r'(\d+\.?\d*)').astype(float).sum()[0]
except:
    total_w = 0
render_muscle_sidebar(total_w)

# --- ダッシュボード ---
c1, c2 = st.columns(2)
with c1:
    st.metric("ベンチプレス1RM基準", "115.0 kg", delta="NEW RECORD!")
with c2:
    st.metric("次の目標 (120kgまで)", "あと 5.0 kg")

# --- 🏋️ AIメニュー生成 ---
st.markdown("---")
prog = st.selectbox("プログラム", ["ベンチプレス強化(胸・腕)", "スクワット強化(脚)", "デッドリフト強化(背中・脚)", "筋力増強"])

if st.button("🚀 115kg基準で今日のメニューを算出"):
    with st.spinner("石井先生、岡田先生の理論に基づき計算中..."):
        # AIプロンプトに115kgを反映
        api_key = st.secrets["GOOGLE_API_KEY"]
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        system = (
            f"あなたは最高のパートナー『Muscle Mate』です。明るい口調で話します。\n"
            f"重要：ベンチプレスMAXは115kgです。これを100%として、漸進性過負荷の原則に基づきメニューを出せ。\n"
            "石井直方先生、バズーカ岡田先生の理論を引用して解説してください。"
        )
        payload = {"contents": [{"parts": [{"text": f"{system}\n\n指令：{prog}の今日のメニューを提案して。"}]}]}
        res = requests.post(url, json=payload)
        st.session_state['ai_resp'] = res.json()['candidates'][0]['content']['parts'][0]['text']

if 'ai_resp' in st.session_state:
    st.markdown(st.session_state['ai_resp'])

# --- 📝 記録フォーム ---
st.markdown("---")
st.subheader("📝 実績を記録して積載量を増やそう！")
with st.form("workout_log"):
    logs = []
    total_today = 0
    for i in range(3):
        col_ex, col_w, col_r, col_s = st.columns([3, 1, 1, 1])
        with col_ex: ex = st.text_input(f"種目 {i+1}", value="ベンチプレス" if i==0 else "")
        with col_w: w = st.number_input("kg", key=f"w{i}", step=2.5)
        with col_r: r = st.number_input("回数", key=f"r{i}", step=1)
        with col_s: s = st.number_input("セット", key=f"s{i}", step=1)
        if ex and w > 0:
            total_today += w * r * s
            logs.append(f"{ex}:{w}kgx{r}x{s}")
            
    if st.form_submit_button("🔥 記録を聖典に刻印！"):
        if sheet and logs:
            sheet.append_row([datetime.now().strftime("%Y-%m-%d"), prog, ", ".join(logs), f"{total_today}kg"])
            st.balloons()
            st.success(f"お疲れ様でした！今日は新たに {total_today}kg の積載に成功！")
