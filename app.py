import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. 聖典の同期 ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s_acc, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except Exception as e:
        return None

# --- 2. 有料枠 AIエンジン（種目抽出用プロンプト） ---
def call_god_mode_ai(prompt, context_data=""):
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '')
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    system_instruction = (
        "あなたは最強のコーチ『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。\n"
        "【絶対ルール】\n"
        "1. ベンチプレス1RM 103.5kg基準。過去データに基づき詳細なメニューを出せ。\n"
        "2. 脚の日は最後に腹筋を追加せよ。\n"
        "3. 🔱分析根拠を述べ、メニューは必ず箇条書きかテーブル形式で提示せよ。"
    )
    payload = {"contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=30)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "🔱接続エラー。"

# --- 3. UI 構築 ---
st.set_page_config(page_title="GOD-MODE ANALYST", page_icon="🔱", layout="wide")
st.title("🔱 GOD-MODE: ADVANCED LOGGING")

# セッション状態の初期化
if 'menu_items' not in st.session_state:
    st.session_state['menu_items'] = ["ベンチプレス", "スクワット", "デッドリフト"]

# プログラム選択
col_a, col_b = st.columns(2)
with col_a:
    program = st.selectbox("プログラム", ["ベンチプレス強化", "スクワット強化", "デッドリフト強化", "筋肥大", "筋力増強"])
with col_b:
    targets = st.multiselect("対象部位", ["胸", "背中", "脚", "肩", "腕", "腹筋"], default=["胸"])

if st.button("🔱 メニューを算出"):
    with st.spinner("分析中..."):
        response = call_god_mode_ai(f"{program}, 部位:{targets}, 103.5kg基準")
        st.session_state['last_response'] = response
        # 回答から種目名っぽいものを抽出してリスト化
        extracted = re.findall(r"[*・]\s*([^\s(（]+)", response)
        if extracted:
            st.session_state['menu_items'] = list(dict.fromkeys(extracted)) # 重複削除
        st.markdown("---")
        st.markdown(response)

# --- 4. 【本命】動的・複数種目記録セクション ---
st.markdown("---")
st.subheader("🔱 本日の調練実績を記録せよ")

# 最大5種目まで一度に入力できる欄を作成
log_data_list = []
for i in range(5):
    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
    with c1:
        # AIが提案した種目、または手入力をプルダウンで
        ex_name = st.selectbox(f"種目 {i+1}", ["(未選択)"] + st.session_state['menu_items'], key=f"ex_{i}")
    with c2:
        ex_weight = st.text_input("重量", key=f"w_{i}", placeholder="kg")
    with c3:
        ex_reps = st.selectbox("回数", [str(n) for n in range(1, 31)] + ["MAX"], key=f"r_{i}")
    with c4:
        ex_sets = st.selectbox("セット", [str(n) for n in range(1, 11)], key=f"s_{i}")
    
    if ex_name != "(未選択)" and ex_weight:
        log_data_list.append(f"{ex_name}: {ex_weight}kg x {ex_reps}reps x {ex_sets}sets")

if st.button("🔱 聖典（全実績一括）に刻印"):
    if log_data_list:
        sheet = connect_to_sheet()
        if sheet:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            full_log = " / ".join(log_data_list)
            sheet.append_row([now, program, ", ".join(targets), full_log])
            st.success(f"🔱 記録完了：{full_log}")
    else:
        st.warning("種目と重量を入力せよ。")

# --- 5. 履歴表示 & RPM ---
st.markdown("---")
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
    st.metric("推定1RM", f"{(w * (1 + r/30)):.2f} kg")
