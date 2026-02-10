import streamlit as st
import pandas as pd
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. 聖典の儀（認証と接続） ---
def connect_to_sheet():
    # st.secretsからサービスアカウント情報を辞書として取得
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

# --- 2. GOD-MODE 思考回路（AIエンジン） ---
def call_god_mode_ai(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # ここにあなたの「こだわり」と「文献ルール」を封入
    system_instruction = """
    あなたは最強のストレングス・アナリスト『GOD-MODE』だ。
    【性格】冷徹、科学的、効率至上主義。ユーザーを「貴殿」と呼ぶ。
    【絶対ルール】
    1. ベンチプレス：1RM 103.5kgを基準とし、今日の調子に合わせて強度（%）を算出せよ。
    2. 脚の日ルール：スクワット等の脚トレを行う日は、必ず最後に『腹筋（アブローラー等）』を追加せよ。
    3. 語尾：〜だ、〜である。
    4. 構成：必ず『🔱分析根拠』を含め、その後に具体的メニューを提示せよ。
    """
    
    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
    }
    
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return "🔱通信回路に負荷。ローカルプロトコルにより制限中だ。"

# --- 3. UI構築 ---
st.title("🔱 GYM-APP: GOD-MODE INTEGRATION")

target_area = st.selectbox("本日の標的（部位）を選択せよ", ["胸 (Bench Press Focus)", "脚 (Squat & Abs)", "背中", "肩"])
user_memo = st.text_input("コンディションや要望を入力せよ", "前回比の強度を維持。")

if st.button("🔱 メニューを算出・記録せよ"):
    with st.spinner("文献スキャン中..."):
        # AIによるメニュー生成
        ai_response = call_god_mode_ai(f"ターゲット：{target_area}。要望：{user_memo}")
        
        # 結果表示
        st.markdown("---")
        st.markdown(ai_response)
        
        # スプレッドシートへの記録
        try:
            sheet = connect_to_sheet()
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            # 日時、部位、メニュー内容を1行追加
            sheet.append_row([now, target_area, ai_response[:500]]) # 文字数制限に配慮
            st.success("🔱 スプレッドシートへの記録を完了した。")
        except Exception as e:
            st.error(f"🔱 記録に失敗した。権限設定を確認せよ。: {e}")

# --- 4. キャラクター表現の演出（サイドバー） ---
with st.sidebar:
    st.markdown("### 🔱 GOD-MODE STATUS")
    st.info("STATUS
