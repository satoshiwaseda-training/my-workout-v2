import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

# --- 1. 聖典の記録（Google Sheets 接続） ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except Exception as e:
        st.sidebar.error(f"🔱 シート同期回路エラー：{e}")
        return None

# --- 2. 有料枠専用 AIエンジン (429/404 完全封殺版) ---
def call_god_mode_ai(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '')
    
    # 有料プランで最も推奨される安定版エンドポイント
    # まずは最高性能の 2.0-flash を試行
    models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash"]
    
    system_instruction = (
        "あなたは最強のストレングスアナリスト『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。\n"
        "【絶対ルール】\n"
        "1. ベンチプレス：1RM 103.5kgを基準に、今日のセットを算出せよ。\n"
        "2. 脚の日：脚トレを行う日は、必ず最後に腹筋（アブローラー等）を3セット以上追加せよ。\n"
        "3. 🔱分析根拠：回答の文頭に、文献に基づいた理論的根拠を必ず記述せよ。"
    )

    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
    }

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}"
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=25)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text']
        except:
            continue
            
    # 全滅した場合のみエラー詳細を出す
    return f"🔱接続拒絶：全モデルが応答しません。Google AI StudioのPlan設定でプロジェクトがPaidに紐付いているか再確認せよ。"

# --- 3. メイン UI 構築 ---
st.set_page_config(page_title="GOD-MODE SUPREME", page_icon="🔱", layout="wide")

# スタイル設定
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; background-color: #ff4b4b; color: white; font-weight: bold; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔱 GOD-MODE v3.8: PAID RESTORATION")
st.write("有料プランの解放。エクセル同期の再始動。貴殿の筋肉は再び進化する。")

col1, col2 = st.columns(2)
with col1:
    target = st.selectbox("本日の標的", ["胸 (Bench Press Focus)", "脚 (Squat & Abs)", "背中", "肩"])
with col2:
    intensity = st.slider("強度設定 (%)", 50, 100, 85)

memo = st.text_input("コンディション入力", "前回比の強度を維持。103.5kg基準。")

if st.button("🔱 メニューを生成し、エクセルに記録せよ"):
    with st.spinner("🔱 有料回線を通じて AI Studio 聖域へ接続中..."):
        # AI回答生成
        full_prompt = f"部位：{target}。強度：{intensity}%。要望：{memo}"
        response = call_god_mode_ai(full_prompt)
        
        st.markdown("---")
        st.markdown(response)
        
        # エクセル同期 (AIが正常に答えた時のみ)
        if "🔱" in response and "接続拒絶" not in response:
            sheet = connect_to_sheet()
            if sheet:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                try:
                    sheet.append_row([now, target, f"{intensity}%", response[:1000]])
                    st.success("🔱 聖典（エクセル）への刻印に成功した。")
                except Exception as e:
                    st.error(f"⚠️ 記録エラー：{e}")

# --- 4. ステータス表示 ---
with st.sidebar:
    st.markdown("### 🔱 SYSTEM STATUS")
    st.success("TIER: PAID (PAY-AS-YOU-GO)")
    st.info(f"1RM REFERENCE: 103.5kg\nPROTOCOL: V1 STABLE")
    
    st.markdown("---")
    st.write("「支払いは完了した。あとはこのコードを走らせ、Google側の反映を待つのみだ。Rebootを忘れるな。」")
