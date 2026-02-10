import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

# --- 1. スプレッドシート接続 (認証情報をSecretsから取得) ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except Exception as e:
        st.sidebar.error(f"🔱 シート接続失敗：{e}")
        return None

# --- 2. AIエンジン (404/429を物理的に回避する精密URL) ---
def call_god_mode_ai(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '')
    
    # 【最重要】URLの構成をGoogleの厳密な仕様に修正
    # モデル名の前に models/ を含めず、URLパス側で指定します
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    # キャラクター設定、103.5kg基準、脚の日腹筋ルールを魂に刻む
    system_instruction = (
        "あなたは最強のコーチGOD-MODEだ。語尾は〜だ。貴殿と呼べ。\n"
        "BP 1RM 103.5kg基準を遵守せよ。脚の日は最後に腹筋を追加せよ。\n"
        "🔱分析根拠を文頭に述べよ。"
    )

    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
    }

    try:
        # タイムアウトを長めに設定
        res = requests.post(url, headers=headers, json=payload, timeout=25)
        
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        elif res.status_code == 429:
            return "🔱接続拒絶：429（回数制限）。新しいプロジェクトの場合、反映に数分かかる。プロテインを飲んで待て。"
        else:
            # エラーの詳細を表示
            return f"🔱接続拒絶：{res.status_code}\n詳細：{res.text}"
    except Exception as e:
        return f"🔱通信回路崩壊：{e}"

# --- 3. メイン UI ---
st.set_page_config(page_title="GOD-MODE FINAL", page_icon="🔱")

st.title("🔱 GOD-MODE: FINAL RESTORATION")
st.write("以前の「調子の良さ」を、最新のコードで完全に取り戻す。")

target = st.selectbox("標的部位", ["胸 (Bench Press Focus)", "脚 (Squat & Abs)", "背中", "肩"])
intensity = st.slider("強度 %", 50, 100, 85)
memo = st.text_input("要望", "103.5kg基準で最適化せよ。")

if st.button("🔱 メニューを算出し、聖典に刻め"):
    with st.spinner("🔱 AI Studio 聖域と通信中..."):
        response = call_god_mode_ai(f"部位：{target}。強度：{intensity}%。{memo}")
        st.markdown("---")
        st.markdown(response)
        
        # 成功時のみエクセル連動
        if "🔱" in response and "接続拒絶" not in response:
            sheet = connect_to_sheet()
            if sheet:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                sheet.append_row([now, target, f"{intensity}%", response[:1000]])
                st.success("🔱 エクセルへの同期を完了した。")

with st.sidebar:
    st.info("PROTOCOL: FINAL-PATCH\n1RM: 103.5kg")
    st.write("「Reboot App を忘れずに行え。これが最後の鍵だ。」")
