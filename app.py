import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. AIエンジン (404の隙を与えない厳格設定) ---
def call_god_mode_ai(prompt):
    # Secretsから洗浄済みのキーを取得
    api_key = str(st.secrets["GOOGLE_API_KEY"]).strip().replace('"', '')
    
    # 2026年現在、AI Studioの新規キーで最も成功率が高いURL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # 貴殿の聖典（文献・ベンチプレス103.5kg・脚の日腹筋）をAIの魂に刻む
    system_instruction = (
        "あなたは最強のストレングスコーチ『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。"
        "ベンチプレス1RM 103.5kg基準を遵守。脚の日は腹筋必須。"
        "文献に基づき『🔱分析根拠』を述べ、その後にメニューを提示せよ。"
    )

    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            # 404が万が一出た場合の、詳細な原因切り分け
            return f"🔱接続拒絶：{res.status_code}\n詳細：{res.text}\n※新しいプロジェクトでキーを作り直したか確認せよ。"
    except Exception as e:
        return f"🔱通信回路崩壊：{e}"

# --- 2. エクセル連動 (AIの処理を邪魔しないよう独立) ---
def log_to_sheet(target, content):
    try:
        s_acc = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s_acc, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        sheet = gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
        sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), target, content[:500]])
        return True
    except: return False

# --- 3. メインUI ---
st.set_page_config(page_title="GOD-MODE FINAL", page_icon="🔱")
st.title("🔱 GOD-MODE: THE RESTORATION")

target = st.selectbox("標的部位を選択", ["胸 (Bench Press Focus)", "脚 (Squat & Abs)", "背中", "肩"])
memo = st.text_input("コンディション", "前回比の強度を維持。聖典に従え。")

if st.button("🔱 知能を再起動せよ"):
    with st.spinner("🔱 AI Studio の聖域にアクセス中..."):
        response = call_god_mode_ai(f"ターゲット：{target}。要望：{memo}")
        st.markdown("---")
        st.markdown(response)
        
        # 成功時のみエクセル連動
        if "🔱" in response and "接続拒絶" not in response:
            if log_to_sheet(target, response):
                st.success("🔱 記録完了。知能とデータは統合された。")

with st.sidebar:
    st.info("PROTOCOL: RESTORE-COMPLETE\n1RM: 103.5kg\nMODE: GOD-MODE ANALYST")
    st.write("「『NEW project』のキー。それこそが、私を封じ込めている404の壁を壊す唯一の槌だ。」")
