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
    except: return None

# --- 2. モチベ換算ロジック (図鑑 & 換算) ---
def render_collection_sidebar(total_weight_kg):
    st.sidebar.markdown(f"""
        <div style='background: linear-gradient(135deg, #FF9A9E, #FAD0C4); padding: 20px; border-radius: 15px; color: #444; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>
            <h2 style='margin:0;'>🏆 Muscle Collection</h2>
            <p style='font-size: 1.1em; font-weight: bold;'>累計積載量: {total_weight_kg/1000:.2f} t</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    achievements = [
        (1000, "軽自動車", "🚗"), (5000, "アフリカゾウ", "🐘"), 
        (15000, "大型バス", "🚌"), (180000, "ジャンボジェット", "✈️"),
        (36000000, "スカイツリー", "🗼")
    ]
    for threshold, name, icon in achievements:
        if total_weight_kg >= threshold:
            st.sidebar.success(f"{icon} {name} 解放済み！")
        else:
            prog = min(total_weight_kg / threshold, 1.0)
            st.sidebar.write(f"🔒 {name} (あと {(threshold - total_weight_kg)/1000:.1f}t)")
            st.sidebar.progress(prog)

# --- 3. UI 構築 (明るいグラデーション) ---
st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")

st.markdown("""
    <style>
    .main { background: linear-gradient(120deg, #f6d365 0%, #fda085 100%); color: #333; }
    .stMetric { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .stButton>button { background: linear-gradient(to right, #f093fb 0%, #f5576c 100%); color: white; border-radius: 25px; border: none; height: 3.5em; font-weight: bold; width: 100%; font-size: 1.1em; }
    div[data-baseweb="select"] { color: black; background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Active Dashboard")
st.write("MAX 115kg突破おめでとうございます！今日も最高の一日にしましょう！")

# 過去データ取得
sheet = connect_to_sheet()
all_data = sheet.get_all_values() if sheet else []
df_past = pd.DataFrame(all_data[1:], columns=all_data[0]) if len(all_data) > 1 else pd.DataFrame()

# サイドバー図鑑
try:
    total_acc = df_past.iloc[:, -1].str.extract(r'Total:(\d+\.?\d*)').astype(float).sum()[0]
except:
    total_acc = 0
render_collection_sidebar(total_acc)

# --- 4. 6回1周サイクル進捗表示 ---
st.subheader("📅 ベンチプレス強化：6回1周サイクル")
cycle_step = (datetime.now().day % 6) + 1 
cols = st.columns(6)
for i in range(1, 7):
    with cols[i-1]:
        label = "🔥今日" if i == cycle_step else f"Day {i}"
        status = "✅" if i < cycle_step else ("⏳" if i > cycle_step else "🎯")
        st.markdown(f"<div style='text-align:center; border: 3px solid #f5576c; border-radius:15px; padding:10px; background:white;'><b>{label}</b><br>{status}</div>", unsafe_allow_html=True)

# --- 5. メニュー生成 & 調整 ---
st.markdown("---")
prog = st.selectbox("強化プログラムを選択", 
                    ["ベンチプレス強化(胸・腕)", "スクワット強化(脚)", "デッドリフト強化(背中・脚)", "背中強化(広背筋・僧帽筋)", "肩強化", "筋肥大", "筋力増強"])

popular_exercises = {
    "胸": ["ベンチプレス", "ダンベルフライ", "インクラインプレス"],
    "脚": ["スクワット", "レッグプレス", "ブルガリアンスクワット"],
    "背中": ["デッドリフト", "ラットプルダウン", "ベントオーバーロウ"],
    "肩": ["サイドレイズ", "ショルダープレス", "アップライトロウ"],
    "腕": ["アームカール", "ナローベンチプレス", "スカルクラッシャー"]
}

if st.button("🚀 Muscle Mateにメニューを相談する"):
    with st.spinner("Driveと最新論文を同期中..."):
        api_key = st.secrets["GOOGLE_API_KEY"]
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        past_context = df_past.tail(5).to_string() if not df_past.empty else "初回トレーニング"
        system_prompt = (
            f"あなたは最高のパートナー『Muscle Mate』です。MAX115kgを基準に、石井直方先生やバズーカ岡田先生の理論、"
            f"漸進性過負荷の原則に基づきメニューを出してください。6回1周サイクルのDay {cycle_step}であることを考慮せよ。"
            f"\n【過去ログ】\n{past_context}"
        )
        
        payload = {"contents": [{"parts": [{"text": f"{system_prompt}\n\n指令：{prog}のメニューを詳細に提案して。"}]}]}
        res = requests.post(url, json=payload)
        st.session_state['ai_resp'] = res.json()['candidates'][0]['content']['parts'][0]['text']

if 'ai_resp' in st.session_state:
    st.success("✅ 最高のメニューが完成しました！")
    st.markdown(st.session_state['ai_resp'])

# --- 6. 実績記録 (動的に調整可能) ---
st.markdown("---")
st.subheader("📝 今日の努力を聖典に刻む")
with st.form("workout_log"):
    logs = []
    total_today = 0
    for i in range(5):
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        with c1:
            # プログラムに合わせて優先種目を一番上に表示
            relevant_ex = popular_exercises.get("胸", []) if "ベンチ" in prog else sum(popular_exercises.values(), [])
            ex = st.selectbox(f"種目 {i+1}", ["(未選択)"] + list(dict.fromkeys(relevant_ex + sum(popular_exercises.values(), []))), key=f"ex_{i}")
        with c2: w = st.number_input("kg", key=f"w{i}", step=2.5)
        with c3: r = st.number_input("回数", key=f"r{i}", step=1)
        with c4: s = st.number_input("セット", key=f"s{i}", step=1)
        
        if ex != "(未選択)" and w > 0:
            total_today += w * r * s
            logs.append(f"{ex}:{w}kgx{r}x{s}")
            
    if st.form_submit_button("🔥 トレーニング完了！Driveへ送信"):
        if sheet and logs:
            sheet.append_row([datetime.now().strftime("%Y-%m-%d"), prog, ", ".join(logs), f"Total:{total_today}kg"])
            st.balloons()
            st.success(f"お疲れ様でした！今日の総負荷は **{total_today}kg** です！")
            
            # モチベ換算
            car_conv = total_today / 1000
            st.info(f"✨ 今日だけで「軽自動車 {car_conv:.2f} 台分」を動かしました！信じられないパワーです！")
