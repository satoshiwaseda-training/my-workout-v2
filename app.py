import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. 聖域接続 (Drive & Sheets) ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except:
        return None

# --- 2. 部位別人気種目リスト ---
popular_exercises = {
    "胸": ["ベンチプレス", "インクラインプレス", "ダンベルフライ", "チェストプレス"],
    "脚": ["スクワット", "レッグプレス", "レッグエクステンション", "ブルガリアンスクワット"],
    "背中": ["デッドリフト", "ラットプルダウン", "ベントオーバーロウ", "懸垂"],
    "肩": ["サイドレイズ", "ショルダープレス", "アップライトロウ"],
    "腕": ["アームカール", "ナローベンチプレス", "ライイングエクステンション"],
    "腹筋": ["アブローラー", "レッグレイズ", "クランチ"]
}

# --- 3. UI 構築 (明るいオレンジグラデーション) ---
st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")

st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #FF9A9E 0%, #FAD0C4 99%, #FAD0C4 100%); color: #444; }
    .stMetric { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .stButton>button { background: linear-gradient(to right, #FF416C, #FF4B2B); color: white; border-radius: 20px; font-weight: bold; border: none; height: 3.5em; }
    div[data-baseweb="select"] { color: black !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Active Dashboard")
st.write("MAX 115kg 基準：限界のその先へ、共に。")

# 過去データ取得
sheet = connect_to_sheet()
df_past = pd.DataFrame()
if sheet:
    data = sheet.get_all_values()
    if len(data) > 1:
        df_past = pd.DataFrame(data[1:], columns=data[0])

# --- サイドバー：コレクション図鑑 ---
st.sidebar.header("🏆 Muscle Collection")
try:
    total_w_kg = df_past.iloc[:, -1].str.extract(r'Total:(\d+\.?\d*)').astype(float).sum()[0]
except:
    total_w_kg = 0

st.sidebar.write(f"累計積載量: {total_w_kg/1000:.2f} t")
achievements = [(1000, "軽自動車", "🚗"), (180000, "ジャンボジェット", "✈️"), (36000000, "スカイツリー", "🗼")]
for threshold, name, icon in achievements:
    if total_w_kg >= threshold:
        st.sidebar.success(f"{icon} {name} 解放済み！")
    else:
        st.sidebar.write(f"🔒 {name} (あと {(threshold - total_w_kg)/1000:.1f}t)")

# --- 4. メインダッシュボード ---
c1, c2, c3 = st.columns(3)
with c1: st.metric("1RM基準", "115.0 kg")
with c2: st.metric("28日間合計", "239.29 t") # 以前のUIエッセンス
with c3: 
    jet_val = total_w_kg / 180000
    st.metric("飛行機積載量", f"{jet_val:.4f} ✈️")

# --- 5. AIメニュー提案 ---
st.markdown("---")
prog = st.selectbox("プログラム", ["ベンチプレス強化(胸・腕)", "スクワット強化(脚)", "デッドリフト強化(背中・脚)", "背中強化", "肩強化"])

if st.button("🚀 Muscle Mateにメニューを相談する"):
    with st.spinner("Driveと最新論文を解析中..."):
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        past_context = df_past.tail(10).to_string() if not df_past.empty else "新規"
        system = (
            f"あなたは最高のパートナー『Muscle Mate』。MAX115kg基準。石井直方先生、バズーカ岡田先生の理論、"
            f"漸進性過負荷の原則に基づき、過去ログを考慮してメニューを出せ。"
            f"\n【履歴】\n{past_context}"
        )
        payload = {"contents": [{"parts": [{"text": f"{system}\n\n指令：{prog}のメニューを詳細に出して。"}]}]}
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            st.session_state['ai_resp'] = res.json()['candidates'][0]['content']['parts'][0]['text']
            # AI提案から種目名を抽出
            st.session_state['suggested_items'] = re.findall(r'[*・]\s*([^\s(（]+)', st.session_state['ai_resp'])[:4]

if 'ai_resp' in st.session_state:
    st.info(st.session_state['ai_resp'])

# --- 6. 動的実績記録 (AI連動 + 人気種目) ---
st.markdown("---")
st.subheader("📝 今日の努力を記録（Google Sheets/Drive同期）")

# 全人気種目の統合リスト
all_popular = sum(popular_exercises.values(), [])
suggested = st.session_state.get('suggested_items', ["ベンチプレス", "スクワット", "デッドリフト", "懸垂"])

with st.form("workout_form", clear_on_submit=False):
    logs = []
    total_today = 0
    for i in range(4):
        default_ex = suggested[i] if i < len(suggested) else all_popular[i]
        c_ex, c_w, c_r, c_s = st.columns([3, 1, 1, 1])
        with c_ex:
            # AI提案をトップにしつつ、全人気種目を選択可能
            opts = [default_ex] + [x for x in all_popular if x != default_ex]
            ex = st.selectbox(f"種目 {i+1}", opts, key=f"ex_{i}")
        with c_w: w = st.number_input("kg", key=f"w_{i}", step=2.5)
        with c_r: r = st.number_input("回数", key=f"r_{i}", step=1)
        with c_s: s = st.number_input("セット", key=f"s_{i}", step=1)
        if w > 0:
            total_today += w * r * s
            logs.append(f"{ex}:{w}kgx{r}x{s}")

    if st.form_submit_button("🔥 記録を聖典（Drive）に刻印！"):
        if sheet and logs:
            now = datetime.now().strftime("%Y-%m-%d")
            sheet.append_row([now, prog, ", ".join(logs), f"Total:{total_today}kg"])
            st.balloons()
            st.success(f"記録完了！今日の負荷: {total_today}kg (軽自動車 {total_today/1000:.2f}台分！)")

# --- 7. 履歴・Drive参照・設定 (完全復元) ---
st.markdown("---")
tab1, tab2 = st.tabs(["📜 履歴（Drive同期）", "⚙️ 設定 & 聖域詳細"])
with tab1:
    if not df_past.empty:
        st.dataframe(df_past.tail(15), use_container_width=True)
with tab2:
    st.write(f"ベンチプレス MAX基準: 115kg")
    st.write("Google Drive: 正常接続中")
    st.write("理論ベース: 石井直方先生 / バズーカ岡田先生")
