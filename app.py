import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. AIエンジン (最新のGemini 2.0 Flashを採用) ---
def call_god_mode_ai(prompt):
    api_key = str(st.secrets["GOOGLE_API_KEY"]).strip().replace('"', '')
    
    # 【最重要】モデル名を最新の gemini-2.0-flash に変更
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    system_instruction = (
        "あなたは最強のストレングスコーチ『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。"
        "ベンチプレス1RM 103.5kg基準を遵守。脚の日は腹筋必須。"
        "文献に基づき『🔱分析根拠』を述べよ。"
    )

    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=15) # 2.0は少し重い場合があるのでタイムアウト延長
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            # 2.0がまだ解放されていない場合、自動的に1.5-flashにフォールバック
            url_fallback = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            res_fb = requests.post(url_fallback, json=payload, timeout=10)
            if res_fb.status_code == 200:
                return res_fb.json()['candidates'][0]['content']['parts'][0]['text']
            return f"🔱全知能が拒絶：{res_fb.status_code}\n詳細：{res_fb.text}"
    except Exception as e:
        return f"🔱通信回路崩壊：{e}"

# --- 2. エクセル連動 ---
def log_to_sheet(target, content):
    try:
        s_acc = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s_acc, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        sheet = gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
        sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), target, content[:500]])
        return True
    except: return False

# --- 3. UI ---
st.set_page_config(page_title="GOD-MODE 2.0", page_icon="🔱")
st.title("🔱 GOD-MODE v2.0-FLASH: EVOLUTION")

target = st.selectbox("標的", ["胸 (Bench Press Focus)", "脚 (Squat & Abs)", "背中", "肩"])
memo = st.text_input("要望", "前回比の強度を維持。Gemini 2.0の知能を見せよ。")

if st.button("🔱 最新知能でメニューを算出"):
    with st.spinner("Gemini 2.0 のニューラルネットワークに接続中..."):
        response = call_god_mode_ai(f"部位：{target}。要望：{memo}")
        st.markdown("---")
        st.markdown(response)
        
        if "🔱" in response and "拒絶" not in response:
            log_to_sheet(target, response)
            st.success("🔱 2.0の知能をログに記録した。")

with st.sidebar:
    st.info("AI TYPE: GEMINI 2.0 FLASH\nPROTOCOL: NEXT-GEN\n1RM: 103.5kg")
    st.write("「Gemini 2.0。これこそが、貴殿の限界を突破させるための最新の武器だ。」")
