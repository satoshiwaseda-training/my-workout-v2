import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

# --- 1. 認証と接続 ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except:
        return None

# --- 2. 404を回避する「二段階」AIエンジン ---
def call_god_mode_ai(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # 試行するモデルの優先順位
    models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    
    system_instruction = (
        "あなたは最強のアナリスト『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。"
        "BP 103.5kg基準を遵守。脚の日は腹筋を強制せよ。🔱分析根拠を必ず書け。"
    )

    for model_name in models:
        # 404を回避するための最新のURL形式
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
        }
        
        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text']
            # 404が出た場合は、次のモデルを試す
            continue 
        except:
            continue
            
    return "🔱全てのモデルが拒絶。APIキーがAI Studioで有効化されているか確認せよ。"

# --- 3. UI構築 ---
st.set_page_config(page_title="GOD-MODE AI", page_icon="🔱")
st.title("🔱 GOD-MODE v2.1: 404-BYPASS")

target_area = st.selectbox("標的を選択せよ", ["胸 (Bench Press Focus)", "脚 (Squat & Abs)", "背中", "肩"])
user_memo = st.text_input("コンディション", "前回比の強度を維持。")

if st.button("🔱 メニューを算出せよ"):
    with st.spinner("AI回路をバイパス中..."):
        ai_response = call_god_mode_ai(f"部位：{target_area}。要望：{user_memo}")
        st.markdown("---")
        st.markdown(ai_response)
        
        # スプレッドシート記録
        sheet = connect_to_sheet()
        if sheet and "🔱" in ai_response: # 正常生成時のみ記録
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            sheet.append_row([now, target_area, ai_response[:1000]])
            st.success("🔱 記録完了だ。")

with st.sidebar:
    st.markdown("### 🔱 STATUS")
    st.info("PROTOCOL: V1-BETA/FALLBACK\nREF: 1RM 103.5kg")
    st.write("「404という壁すら、筋肉の成長のための負荷に過ぎない。」")
