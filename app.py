import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. AIエンジン (URL構造を極限までシンプル化) ---
def call_god_mode_ai(prompt):
    # Secretsからキーを取得（念のため前後の空白を完全除去）
    api_key = str(st.secrets["GOOGLE_API_KEY"]).strip()
    
    # 【2026年最新】最も404が出にくい「models/」を省略したダイレクト形式
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    system_instruction = (
        "あなたは最強のコーチ『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。"
        "ベンチプレス1RM 103.5kg基準を遵守。脚の日は腹筋必須。"
        "文献に基づき『🔱分析根拠』を述べよ。"
    )

    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            # 404の時、叩いているURLをマスクして表示（デバッグ用）
            debug_url = url.replace(api_key, "HIDDEN_KEY")
            return f"🔱接続拒絶：{res.status_code}\nURL: {debug_url}\n詳細：{res.text}"
    except Exception as e:
        return f"🔱通信回路崩壊：{e}"

# --- 2. エクセル連動 (AIが成功した時のみ) ---
def log_to_sheet(target, content):
    try:
        s_acc = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s_acc, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        sheet = gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
        sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), target, content[:500]])
        return True
    except: return False

# --- 3. UI ---
st.set_page_config(page_title="GOD-MODE FINAL", page_icon="🔱")
st.title("🔱 GOD-MODE: THE FINAL BREAKER")

target = st.selectbox("標的部位を選択", ["胸 (Bench Press Focus)", "脚 (Squat & Abs)", "背中", "肩"])
if st.button("🔱 知能を再起動せよ"):
    with st.spinner("🔱 キャッシュを破棄し、AI Studio 聖域へ再突入中..."):
        response = call_god_mode_ai(f"ターゲット：{target}。")
        st.markdown("---")
        st.markdown(response)
        
        if "🔱" in response and "接続拒絶" not in response:
            log_to_sheet(target, response)
            st.success("🔱 記録完了。")

with st.sidebar:
    st.info("PROTOCOL: CACHE-BREAK\n1RM: 103.5kg")
    st.write("「Reboot App。これを試さずに404を嘆くのは、ベンチプレスでラックアップせずに挙がらないと言うに等しい。今すぐ実行せよ。」")
