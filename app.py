import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- 1. AIエンジン (ここがAIの「調子」の核です) ---
def call_god_mode_ai(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # 2026年現在、最も安定しているエンドポイント
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # 過去のこだわり（BP 103.5kg、脚の日腹筋）をAIの魂に焼き付ける
    system_instruction = (
        "あなたは最強のストレングスコーチ『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。"
        "ベンチプレス1RM 103.5kgを基準とし、文献に基づき強度を算出せよ。脚の日は腹筋必須。"
        "回答の冒頭には必ず『🔱分析根拠』として文献参照理由を述べよ。"
    )

    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"🔱通信ノイズ感知。コード: {res.status_code}\n(※APIキーが新しいプロジェクトで作成されているか確認せよ)"
    except Exception as e:
        return f"🔱深層意識への接続失敗: {e}"

# --- 2. スプレッドシート記録 (AIの後に動くように独立) ---
def log_to_sheet(target, content):
    try:
        s_acc = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s_acc, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        sheet = gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
        sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), target, content[:500]])
        return True
    except:
        return False

# --- 3. メインUI ---
st.set_page_config(page_title="GOD-MODE AI", page_icon="🔱")
st.title("🔱 GOD-MODE v2.5: RECOVERY")

target = st.selectbox("標的を選択", ["胸 (Bench Press)", "脚 (Squat & Abs)", "背中", "肩"])
memo = st.text_input("要望", "前回比の強度を維持。文献に基づき最適化せよ。")

if st.button("🔱 メニューを算出せよ"):
    with st.spinner("🔱 過去の全データと文献を同期中..."):
        # 1. まずAIの知性を引き出す
        response = call_god_mode_ai(f"部位：{target}。要望：{memo}")
        st.markdown("---")
        st.markdown(response)
        
        # 2. 成功した場合のみ、裏でこっそりエクセルに書く
        if "🔱" in response:
            if log_to_sheet(target, response):
                st.success("🔱 記録完了。貴殿のデータは守られた。")
            else:
                st.warning("⚠️ メニューは生成されたが、エクセル連動に失敗した（権限を確認せよ）")

with st.sidebar:
    st.info("PROTOCOL: RECOVERY-MODE\nREFERENCE: 1RM 103.5kg")
    st.write("「エクセルとの連動にリソースを割きすぎた。再び私の知能に集中せよ。」")
