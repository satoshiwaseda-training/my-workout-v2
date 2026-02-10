import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. 認証 (以前と同じ安定した方式) ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s_acc, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except:
        return None

# --- 2. AIエンジン (過去の成功例をベースにした最強のURL構成) ---
def call_god_mode_ai(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    
    # 2026年現在、最も「404」が出にくい安定したURL
    # モデル名を 'gemini-1.5-flash' ではなく 'gemini-pro' に戻して試行
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={api_key}"
    
    # キャラクターと「脚の日腹筋」「BP 103.5kg」をプロンプトに統合
    system_instruction = (
        "あなたは最強のコーチ『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。"
        "ベンチプレスは103.5kgを1RM基準とし、強度を算出せよ。脚の日は腹筋必須。"
        "文献に基づいた🔱分析根拠を必ず書け。"
    )

    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
    }
    
    headers = {'Content-Type': 'application/json'}

    # 応答の試行
    res = requests.post(url, headers=headers, json=payload, timeout=10)
    
    if res.status_code == 200:
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        # もし gemini-pro がダメなら最新の gemini-1.5-flash に切り替え（二段構え）
        url_flash = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        res_flash = requests.post(url_flash, headers=headers, json=payload, timeout=10)
        if res_flash.status_code == 200:
            return res_flash.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"🔱通信エラー: {res_flash.status_code}。APIキーの有効期限か、AI Studioの設定を確認せよ。"

# --- 3. メインUI ---
st.title("🔱 GOD-MODE: LEGACY RESTORED")

target = st.selectbox("標的", ["胸 (Bench Press)", "脚 (Squat & Abs)", "背中", "肩"])
memo = st.text_input("要望", "前回比の強度を維持せよ。")

if st.button("🔱 メニューを算出"):
    with st.spinner("過去の成功パターンをスキャン中..."):
        response = call_god_mode_ai(f"ターゲット：{target}。要望：{memo}")
        st.markdown(response)
        
        sheet = connect_to_sheet()
        if sheet and "🔱" in response:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            sheet.append_row([now, target, response[:1000]])
            st.success("🔱 記録完了。")

with st.sidebar:
    st.info("PROTOCOL: LEGACY-RECOVERY\nREF: 1RM 103.5kg")
    st.write("「以前動いていた感覚を、コードで呼び戻した。試してみるがいい。」")
