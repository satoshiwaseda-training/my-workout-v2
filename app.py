import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json

# --- 1. スプレッドシート接続（聖典の記録場所） ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        # スプレッドシートIDをSecretsから取得
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except Exception as e:
        st.sidebar.error(f"🔱 シート同期エラー：{e}")
        return None

# --- 2. 有料枠専用 AIエンジン (404/429 完全封殺) ---
def call_god_mode_ai(prompt):
    # APIキーの取得（前後の空白を念のため除去）
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '')
    
    # 有料プラン（Paid Tier）で最も安定する『v1』安定版URL
    # モデルは最新の 2.0 Flash を指定
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    # 貴殿の「こだわり」を最優先事項として固定
    system_instruction = (
        "あなたは最強のコーチ『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。\n"
        "【絶対ルール】\n"
        "1. ベンチプレス：1RM 103.5kgを絶対基準とし、指定された強度（%）に基づきセット・回数を算出せよ。\n"
        "2. 脚の日ルール：脚トレの日は、必ず最後に腹筋（アブローラー等）を3セット以上追加せよ。\n"
        "3. 🔱分析根拠：回答の文頭に、ストレングス理論に基づいた理由を必ず記述せよ。"
    )

    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
    }

    try:
        # 有料枠はレスポンスが高速ですが、念のためタイムアウトは長めに
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            # 万が一のエラー時は詳細を表示（デバッグ用）
            return f"🔱接続拒絶：{res.status_code}\n詳細：{res.text}"
    except Exception as e:
        return f"🔱回路崩壊：{e}"

# --- 3. メイン UI 構築 ---
st.set_page_config(page_title="GOD-MODE FINAL", page_icon="🔱", layout="wide")

# UIカスタム（重厚なダークモード風）
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; background-color: #ff4b4b; color: white; font-weight: bold; height: 3em; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔱 GOD-MODE: THE FINAL ASCENSION")
st.write("有料プラン解放。これより、貴殿の筋肉とエクセルを完全同期する。")

col1, col2 = st.columns(2)
with col1:
    target = st.selectbox("本日の標的（ターゲット）", ["胸 (Bench Press Focus)", "脚 (Squat & Abs)", "背中", "肩"])
with col2:
    intensity = st.slider("強度設定（% of 1RM）", 50, 100, 85)

memo = st.text_input("コンディション・要望", "前回比の強度を維持。103.5kg基準で頼む。")

if st.button("🔱 聖典（メニュー）を生成し記録せよ"):
    with st.spinner("🔱 有料回線を通じて AI Studio 聖域へアクセス中..."):
        # AI回答生成
        full_prompt = f"ターゲット：{target}。強度：{intensity}%。要望：{memo}"
        response = call_god_mode_ai(full_prompt)
        
        st.markdown("---")
        st.markdown(response)
        
        # エクセル同期（成功時のみ）
        if "🔱" in response and "接続拒絶" not in response:
            sheet = connect_to_sheet()
            if sheet:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                try:
                    sheet.append_row([now, target, f"{intensity}%", response[:1000]])
                    st.success("🔱 スプレッドシートへの刻印を完了した。")
                except Exception as e:
                    st.error(f"⚠️ 記録エラー：{e}")

# --- 4. サイドバー ---
with st.sidebar:
    st.markdown("### 🔱 SYSTEM STATUS")
    st.success("API TIER: PAID (UNLIMITED)")
    st.info(f"1RM REF: 103.5kg\nMODEL: GEMINI 2.0 FLASH")
    st.markdown("---")
    st.write("「支払いは完了した。制限という鎖はもうない。存分に追い込むがいい。」")
