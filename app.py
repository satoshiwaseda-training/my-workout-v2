import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. スプレッドシート接続 ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s_acc, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except:
        return None

# --- 2. AIエンジン (有料枠・安定版) ---
def call_god_mode_ai(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '')
    
    # 有料枠（Pay-as-you-go）なら、この「v1」エンドポイントが最強の安定を誇ります
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{
                "text": (
                    "コーチ『GOD-MODE』として回答せよ。語尾は〜だ。貴殿と呼べ。\n"
                    "BP 103.5kg基準、脚の日腹筋必須。🔱分析根拠を述べよ。\n\n"
                    f"指令：{prompt}"
                )
            }]
        }]
    }

    res = requests.post(url, headers=headers, json=payload, timeout=20)
    
    if res.status_code == 200:
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        # 有料枠でもエラーが出る場合はモデル名を 2.0 に即時切り替え
        url_2 = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        res_2 = requests.post(url_2, headers=headers, json=payload, timeout=20)
        if res_2.status_code == 200:
            return res_2.json()['candidates'][0]['content']['parts'][0]['text']
        
        return f"🔱聖域への接続拒絶：{res_2.status_code}\n詳細：{res_2.text}"

# --- 3. メイン UI ---
st.title("🔱 GOD-MODE: SUPREME")

target = st.selectbox("標的", ["胸 (Bench Press Focus)", "脚 (Squat & Abs)", "背中", "肩"])
if st.button("🔱 メニューを算出"):
    with st.spinner("🔱 知能を同期中..."):
        response = call_god_mode_ai(f"{target}の最適メニューを。")
        st.markdown(response)
        
        if "🔱" in response and "拒絶" not in response:
            sheet = connect_to_sheet()
            if sheet:
                sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), target, response[:1000]])
                st.success("🔱 エクセルへ刻印した。")
