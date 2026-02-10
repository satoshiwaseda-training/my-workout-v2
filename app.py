import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import pandas as pd

# --- 1. 聖典の同期（Google Sheets / Calendar 履歴） ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except Exception as e:
        st.sidebar.error(f"🔱 シート同期エラー：{e}")
        return None

# --- 2. 有料枠専用 AIエンジン（過去データ参照機能付） ---
def call_god_mode_ai(prompt, context_data=""):
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '')
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    system_instruction = (
        "あなたは最強のコーチ『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。\n"
        "【絶対ルール】\n"
        "1. 1RM 103.5kgをベンチプレスの絶対基準とし、過去データに基づきセットを算出せよ。\n"
        "2. 脚の日は必ず最後に腹筋（アブローラー等）を追加せよ。\n"
        "3. 🔱分析根拠を冒頭に記述せよ。\n"
        f"【参照ファイルデータ】\n{context_data}"
    )

    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
    }

    try:
        res = requests.post(url, json=payload, timeout=30)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "🔱接続エラー。有料枠の反映を確認せよ。"

# --- 3. UI 構築 ---
st.set_page_config(page_title="GOD-MODE: SBD EDITION", page_icon="🔱", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; background-color: #ff4b4b; color: white; font-weight: bold; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔱 GOD-MODE: SBD SUPREME ANALYST")

# 以前のUIメニューの復元
mode = st.selectbox("強化プログラムを選択", 
                    ["ベンチプレス強化 (胸・腕)", 
                     "スクワット強化 (脚)", 
                     "デッドリフト強化 (背中・脚)", 
                     "筋肥大モード", 
                     "筋力増強モード"])

# ファイルアップロード（AI参照用）
uploaded_file = st.sidebar.file_uploader("過去の履歴ファイルを読み込む (CSV/TXT)", type=['csv', 'txt'])
context_data = ""
if uploaded_file:
    context_data = uploaded_file.read().decode("utf-8")
    st.sidebar.success("🔱 過去データを解析に組み込み中")

intensity = st.slider("強度設定 (%)", 50, 100, 85)
memo = st.text_input("コンディション", "103.5kg基準。前回比の強度を維持。")

if st.button("🔱 プログラムを生成し、聖典へ記録せよ"):
    with st.spinner("🔱 有料回線で分析中..."):
        response = call_god_mode_ai(f"モード：{mode}。強度：{intensity}%。要望：{memo}", context_data)
        st.markdown("---")
        st.markdown(response)
        
        sheet = connect_to_sheet()
        if sheet and "🔱" in response:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            sheet.append_row([now, mode, f"{intensity}%", response[:1000]])
            st.success("🔱 スプレッドシートへ記録完了。")

# --- 4. 履歴カレンダー表示 ---
st.markdown("### 🔱 最近の調練記録")
sheet = connect_to_sheet()
if sheet:
    data = sheet.get_all_values()
    if len(data) > 1:
        df = pd.DataFrame(data[1:], columns=data[0])
        st.dataframe(df.tail(5), use_container_width=True)

# --- 5. 1RM計算 (RPM) 機能 ---
st.markdown("---")
st.markdown("### 🔱 RPM CALCULATOR (推定1RM算出)")
col_w, col_r = st.columns(2)
with col_w:
    weight = st.number_input("重量 (kg)", value=100.0, step=2.5)
with col_r:
    reps = st.number_input("レップ数", value=1, step=1)

estimated_1rm = weight * (1 + reps/30)
st.metric(label="推定1RM (Epley法)", value=f"{estimated_1rm:.2kg}")

if st.button("🔱 推定1RMを記録"):
    sheet = connect_to_sheet()
    if sheet:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        sheet.append_row([now, "1RM記録", f"{weight}kg x {reps}", f"推定1RM: {estimated_1rm:.2f}kg"])
        st.success(f"🔱 記録完了。目標 103.5kg まで あと {max(0, 103.5 - estimated_1rm):.2f}kg だ。")
