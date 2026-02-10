import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd

# --- 1. 聖典の同期（Google Sheets） ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s_acc, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except Exception as e:
        st.sidebar.error(f"🔱 シート接続エラー：{e}")
        return None

# --- 2. 有料枠 AIエンジン ---
def call_god_mode_ai(prompt, context_data=""):
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '')
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    system_instruction = (
        "あなたは最強のコーチ『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。\n"
        "【絶対ルール】\n"
        "1. ベンチプレス1RM 103.5kg基準。過去データに基づき詳細なメニューを出せ。\n"
        "2. 脚の日は最後に腹筋を追加せよ。\n"
        "3. 🔱分析根拠を述べ、メニューはテーブル形式で提示せよ。\n"
        f"【参照データ】\n{context_data}"
    )
    payload = {"contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=30)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "🔱接続エラー。再起動せよ。"

# --- 3. UI 構築 ---
st.set_page_config(page_title="GOD-MODE ANALYST", page_icon="🔱", layout="wide")
st.title("🔱 GOD-MODE: TOTAL LOGGING SYSTEM")

# サイドバー：過去データ参照
with st.sidebar:
    st.header("🔱 ARCHIVE")
    uploaded_file = st.file_uploader("過去履歴ファイル", type=['csv', 'txt'])
    context_data = uploaded_file.read().decode("utf-8") if uploaded_file else ""
    st.info("PROTOCOL: PAID TIER / 1RM: 103.5kg")

# メインUI：メニュー生成
col_a, col_b = st.columns(2)
with col_a:
    program = st.selectbox("プログラム", ["ベンチプレス強化", "スクワット強化", "デッドリフト強化", "筋肥大", "筋力増強"])
with col_b:
    targets = st.multiselect("対象部位", ["胸", "背中", "脚", "肩", "腕", "腹筋"], default=["胸"])

intensity = st.slider("強度 (%)", 50, 100, 85)
memo = st.text_input("特記事項", "103.5kg基準を遵守せよ。")

if st.button("🔱 メニューを算出"):
    with st.spinner("分析中..."):
        response = call_god_mode_ai(f"{program}, 部位:{targets}, 強度:{intensity}%, {memo}", context_data)
        st.session_state['last_response'] = response
        st.markdown("---")
        st.markdown(response)

# --- 4. 【重要】実績記録セクション（ここを復元しました） ---
st.markdown("---")
st.subheader("🔱 本日の調練実績を記録せよ")
with st.form("log_form"):
    col_i, col_w, col_r, col_s = st.columns([3, 1, 1, 1])
    with col_i:
        ex_name = st.text_input("種目名", placeholder="例：ベンチプレス")
    with col_w:
        ex_weight = st.text_input("重量(kg)", placeholder="100")
    with col_r:
        ex_reps = st.text_input("回数", placeholder="5")
    with col_s:
        ex_sets = st.text_input("セット数", placeholder="3")
    
    submit_log = st.form_submit_button("🔱 聖典（スプレッドシート）に実績を刻む")

    if submit_log:
        sheet = connect_to_sheet()
        if sheet:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            # 実績データを1行にまとめて記録
            log_entry = f"{ex_name}: {ex_weight}kg x {ex_reps}reps x {ex_sets}sets"
            sheet.append_row([now, program, f"{intensity}%", ", ".join(targets), log_entry])
            st.success(f"🔱 記録完了：{log_entry}")

# --- 5. 履歴表示 & RPM ---
tab1, tab2 = st.tabs(["🔱 履歴", "🔱 RPM計算機"])
with tab1:
    sheet = connect_to_sheet()
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            st.dataframe(pd.DataFrame(data[1:], columns=data[0]).tail(10), use_container_width=True)

with tab2:
    w = st.number_input("重量", value=100.0)
    r = st.number_input("回数", value=1)
    rpm = w * (1 + r/30)
    st.metric("推定1RM", f"{rpm:.2f} kg")
