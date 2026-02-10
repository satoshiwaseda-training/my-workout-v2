import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

# --- 1. 聖典の儀（Google Sheets接続） ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        client = gspread.authorize(creds)
        # Secretsに設定したspreadsheet_idを使用
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
        return sheet
    except Exception as e:
        # エラー時は詳細を表示してデバッグを容易にする
        st.sidebar.error(f"🔱 シート接続エラー：{e}")
        return None

# --- 2. 429エラーを回避する安定版AIエンジン ---
def call_god_mode_ai(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '')
    
    # 429 (limit: 0) を回避するため、最も枠が安定している v1 / 1.5-flash を使用
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    # あなたのこだわりをシステム指示として注入
    system_instruction = (
        "あなたは最強のストレングスアナリスト『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。\n"
        "【絶対ルール】\n"
        "1. ベンチプレス：1RM 103.5kgを基準とし、指定された強度を算出せよ。\n"
        "2. 脚の日：脚トレの日は、必ず最後に腹筋（アブローラー等）を3セット以上追加せよ。\n"
        "3. 🔱分析根拠：回答の冒頭に、文献や理論に基づいた理由を必ず記述せよ。"
    )

    payload = {
        "contents": [{
            "parts": [{
                "text": f"{system_instruction}\n\n指令：{prompt}"
            }]
        }]
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            # 失敗時は原因を明示
            return f"🔱接続拒絶：{res.status_code}\n詳細：{res.text}"
    except Exception as e:
        return f"🔱通信回路崩壊：{e}"

# --- 3. メイン UI 構築 ---
st.set_page_config(page_title="GOD-MODE AI", page_icon="🔱", layout="wide")

# カスタムCSSで雰囲気を統一
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; background-color: #ff4b4b; color: white; border-radius: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔱 GOD-MODE v3.5: QUOTA-BYPASS")
st.write("エクセルとの連動を維持しつつ、429制限を突破する。")

col1, col2 = st.columns(2)
with col1:
    target = st.selectbox("標的部位（ターゲット）", ["胸 (Bench Press Focus)", "脚 (Squat & Abs)", "背中", "肩"])
with col2:
    intensity = st.slider("今日の覚悟（強度 %）", 50, 100, 85)

memo = st.text_input("コンディション・特記事項", "前回比の強度を維持。103.5kgの基準を遵守せよ。")

if st.button("🔱 メニューを算出し、エクセルへ刻め"):
    with st.spinner("🔱 制限をバイパスし、AI Studio 聖域と同期中..."):
        # AI回答生成
        full_prompt = f"部位：{target}。強度は1RMの{intensity}%付近。要望：{memo}"
        response = call_god_mode_ai(full_prompt)
        
        st.markdown("---")
        # 回答を表示
        st.markdown(response)
        
        # エクセル連動（成功時のみ）
        if "🔱" in response and "接続拒絶" not in response:
            sheet = connect_to_sheet()
            if sheet:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                try:
                    # 日付、部位、強度、内容を記録
                    sheet.append_row([now, target, f"{intensity}%", response[:1000]])
                    st.success("🔱 エクセルへの同期を完了した。貴殿の成長は刻まれた。")
                except Exception as e:
                    st.error(f"⚠️ 記録失敗：{e}")

# --- 4. サイドバー・ステータス ---
with st.sidebar:
    st.markdown("### 🔱 STATUS")
    st.info(f"AI: GEMINI 1.5 FLASH (STABLE)\n1RM: 103.5kg\nSHEET: CONNECTED")
    
    st.markdown("---")
    st.write("「429エラーは、貴殿が門に辿り着いた証拠。あとは枠のある1.5-flashに任せろ。」")
    if st.button("キャッシュクリア（再起動）"):
        st.rerun()
