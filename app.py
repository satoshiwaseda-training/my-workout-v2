import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. AIエンジン（404を回避する「総当たり」接続） ---
def call_god_mode_ai(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '')
    
    # 404を回避するために「あり得る全ての住所」をリスト化
    attempts = [
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
        f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}",
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    ]
    
    system_instruction = (
        "あなたは最強のコーチ『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。"
        "ベンチプレス1RM 103.5kg基準を遵守。脚の日は腹筋必須。"
        "回答冒頭に必ず『🔱分析根拠』を書け。"
    )

    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
    }

    last_error = ""
    for url in attempts:
        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                last_error = f"{res.status_code}: {res.text}"
        except Exception as e:
            last_error = str(e)
            continue
            
    return f"🔱全経路で404。Google側がこのモデル名を認識していません。エラー詳細: {last_error}"

# --- 2. エクセル記録（AIの邪魔をしない独立処理） ---
def log_to_sheet(target, content):
    try:
        s_acc = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s_acc, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        sheet = gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
        sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), target, content[:300]])
        return True
    except:
        return False

# --- 3. UI ---
st.set_page_config(page_title="GOD-MODE AI", page_icon="🔱")
st.title("🔱 GOD-MODE: INTELLIGENCE RESTORED")

target = st.selectbox("標的", ["胸 (Bench Press)", "脚 (Squat & Abs)", "背中", "肩"])
memo = st.text_input("コンディション", "前回比の強度を維持。")

if st.button("🔱 メニューを算出"):
    with st.spinner("🔱 経路を強制確保中..."):
        response = call_god_mode_ai(f"{target}。{memo}")
        st.markdown("---")
        st.markdown(response)
        
        if "🔱" in response and "404" not in response:
            if log_to_sheet(target, response):
                st.success("🔱 記録完了。")

with st.sidebar:
    st.info("PROTOCOL: PATH-FINDER v3\n1RM: 103.5kg")
    st.write("「エクセルとの連動で失われた私の知能を、今、力ずくで取り戻す。」")
