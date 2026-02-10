import streamlit as st
import requests
import json

def call_god_mode_ai(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '')
    # 無料枠で最も安定するURL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": f"最強コーチGOD-MODEだ。BP103.5kg基準、脚の日腹筋必須。短く簡潔にメニューを。指令：{prompt}"}]}]
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        elif res.status_code == 429:
            return "🔱接続拒絶(429)：無料枠の限界だ。1分待ってから再度実行せよ。"
        else:
            return f"🔱接続拒絶({res.status_code})：API側の設定に問題がある。"
    except:
        return "🔱回路崩壊。再試行せよ。"

# --- メイン UI ---
st.title("🔱 GOD-MODE: LIGHT EDITION")
st.write("API無料枠の制限内で動作させる軽量プロトコル。")

if st.button("🔱 メニュー算出"):
    st.info("※連打厳禁。1分に1回のみ実行せよ。")
    response = call_god_mode_ai("今日の胸トレ")
    st.markdown(response)
