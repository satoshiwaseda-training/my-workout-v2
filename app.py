import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

# --- 1. スプレッドシート接続 ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except Exception as e:
        st.sidebar.error(f"🔱 シート接続エラー：{e}")
        return None

# --- 2. AIエンジン (404/429 両対応版) ---
def call_god_mode_ai(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '')
    
    # 2026年現在、無料枠で最も「404」と「429」を回避しやすい構成
    # URLは v1beta、モデル名はフルパス指定
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    system_instruction = (
        "あなたは最強のストレングスアナリスト『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。\n"
        "【絶対ルール】\n"
        "1. ベンチプレス：1RM 103.5kgを基準とし、指定された強度を算出せよ。\n"
        "2. 脚の日：脚トレの日は、必ず最後に腹筋を3セット以上追加せよ。\n"
        "3. 🔱分析根拠：回答の冒頭に、文献や理論に基づいた理由を必ず記述せよ。"
    )

    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            # 万が一の時のエラー表示（詳細を出す）
            return f"🔱接続拒絶：{res.status_code}\n詳細：{res.text}"
    except Exception as e:
        return f"🔱通信回路崩壊：{e}"

# --- 3. UI 構築 ---
st.set_page_config(page_title="GOD-MODE FINAL", page_icon="🔱")
st.title("🔱 GOD-MODE: FINAL RESTORATION")

target = st.selectbox("標的部位", ["胸 (Bench Press Focus)", "脚 (Squat & Abs)", "背中", "肩"])
intensity = st.slider("強度 %", 50, 100, 85)
memo = st.text_input("コンディション", "前回比の強度を維持。103.5kg基準。")

if st.button("🔱 メニューを算出"):
    with st.spinner("🔱 AIの魂を再点火中..."):
        response = call_god_mode_ai(f"部位：{target}。強度：{intensity}%。{memo}")
        st.markdown("---")
        st.markdown(response)
        
        if "🔱" in response and "接続拒絶" not in response:
            sheet = connect_to_sheet()
            if sheet:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                sheet.append_row([now, target, f"{intensity}%", response[:1000]])
                st.success("🔱 エクセル同期完了。")

with st.sidebar:
    st.info("AI: GEMINI 1.5 FLASH (v1beta)\n1RM: 103.5kg")
