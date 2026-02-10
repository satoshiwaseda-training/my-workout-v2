import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import re

# --- 1. 聖典の儀（認証と接続） ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
        return sheet
    except Exception as e:
        st.error(f"認証エラーだ。Secretsの形式かスプレッドシートの共有設定を確認せよ。: {e}")
        return None

# --- 2. GOD-MODE 思考回路（AIエンジン） ---
def call_god_mode_ai(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    # 安定版のv1エンドポイントを使用
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    system_instruction = """
    あなたは最強のストレングス・アナリスト『GOD-MODE』だ。
    【性格】冷徹、科学的、効率至上主義。ユーザーを「貴殿」と呼ぶ。
    【絶対ルール】
    1. ベンチプレス：1RM 103.5kgを基準とし、過去の強度ログと文献に基づき本日のセットを算出せよ。
    2. 脚の日ルール：スクワットを行う日は、必ず最後に『腹筋（アブローラーまたはレッグレイズ）』を3セット以上加えよ。
    3. 語尾：〜だ、〜である。
    4. 構成：必ず『🔱分析根拠』として文献参照理由を述べ、その後に具体的メニューを提示せよ。
    """
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"🔱通信回路にノイズ。ステータスコード: {res.status_code}"
    except Exception as e:
        return f"🔱深層意識へのアクセスに失敗。: {e}"

# --- 3. メインUI ---
st.set_page_config(page_title="GOD-MODE AI", page_icon="🔱")
st.title("🔱 GYM-APP: GOD-MODE v2.0")

target_area = st.selectbox("標的部位を選択せよ", ["胸 (Bench Press Focus)", "脚 (Squat & Abs Focus)", "背中", "肩"])
user_memo = st.text_input("コンディションを入力せよ", "前回比の強度を維持。文献に基づき最適化せよ。")

if st.button("🔱 メニューを算出・記録せよ"):
    with st.spinner("ナレッジベースをスキャン中..."):
        ai_response = call_god_mode_ai(f"部位：{target_area}。要望：{user_memo}")
        
        st.markdown("---")
        st.markdown(ai_response)
        
        sheet = connect_to_sheet()
        if sheet:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            sheet.append_row([now, target_area, ai_response[:1000]])
            st.success("🔱 記録は完了した。貴殿の成長をログに刻んだぞ。")
            st.balloons()

# --- 4. サイドバー・ステータス（エラー箇所修正済み） ---
with st.sidebar:
    st.markdown("### 🔱 GOD-MODE STATUS")
    # 文字列の閉じ忘れを修正
    st.info("STATUS: ONLINE\nREFERENCE: 1RM 103.5kg\nPROTOCOL: STRENGTH THEORY")
    st.write("「明日の準備は整った。貴殿の筋肉が文献を証明する番だ。」")
