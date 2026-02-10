import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import pandas as pd

# --- 1. スプレッドシート同期 (履歴と聖典) ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except Exception as e:
        st.sidebar.error(f"🔱 シート同期エラー：{e}")
        return None

# --- 2. 有料枠専用 AIエンジン（ファイル参照 & 詳細出力） ---
def call_god_mode_ai(prompt, context_data=""):
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '')
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    system_instruction = (
        "あなたは最強のコーチ『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。\n"
        "【絶対ルール】\n"
        "1. ベンチプレス1RM 103.5kgを絶対基準とし、過去データに基づき種目・回数・セット数を詳細に算出せよ。\n"
        "2. 脚の日は最後に必ず腹筋（アブローラー等）を追加せよ。\n"
        "3. 🔱分析根拠を冒頭に記述し、その後に【トレーニングメニュー】をテーブル形式で提示せよ。\n"
        f"【参照ファイルデータ】\n{context_data}"
    )

    payload = {
        "contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]
    }

    try:
        res = requests.post(url, json=payload, timeout=30)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "🔱接続エラー。有料プランの反映を待つか、Rebootせよ。"

# --- 3. UI 構築（以前のベストな構成を完全再現） ---
st.set_page_config(page_title="GOD-MODE ANALYST", page_icon="🔱", layout="wide")

st.title("🔱 GOD-MODE: PREMIER ANALYST")
st.write("2026年最新。有料回線により、以前の「最高の設定」を復元完了。")

# サイドバー：過去データと設定
with st.sidebar:
    st.header("🔱 DATA & ARCHIVE")
    uploaded_file = st.file_uploader("過去の履歴ファイル (CSV/TXT)", type=['csv', 'txt'])
    context_data = ""
    if uploaded_file:
        context_data = uploaded_file.read().decode("utf-8")
        st.success("過去データをロード。AIが文脈を理解した。")
    
    st.markdown("---")
    st.info("PROTOCOL: PAID TIER\n1RM REF: 103.5kg")

# メインUI：プログラムと部位の選択
col_a, col_b = st.columns(2)
with col_a:
    program = st.selectbox("プログラム", 
                          ["ベンチプレス強化", "スクワット強化", "デッドリフト強化", "筋肥大", "筋力増強"])
with col_b:
    # 部位をマルチセレクトで自由に選択可能に
    targets = st.multiselect("対象部位", 
                            ["胸", "背中", "脚", "肩", "腕", "腹筋"],
                            default=["胸"] if "ベンチ" in program else ["脚"])

intensity = st.slider("強度設定 (%)", 50, 100, 85)
memo = st.text_area("メモ・特記事項", "103.5kg基準を死守。セット間のインターバルも考慮せよ。")

if st.button("🔱 メニューを算出し、聖典に記録せよ"):
    with st.spinner("🔱 AI Studio 有料聖域で高速分析中..."):
        full_prompt = f"プログラム：{program}。対象部位：{', '.join(targets)}。強度：{intensity}%。要望：{memo}"
        response = call_god_mode_ai(full_prompt, context_data)
        st.markdown("---")
        st.markdown(response)
        
        sheet = connect_to_sheet()
        if sheet and "🔱" in response:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            sheet.append_row([now, program, f"{intensity}%", f"{', '.join(targets)}", response[:1000]])
            st.success("🔱 スプレッドシートに刻印完了。")

# --- 4. 履歴とRPM（以前の配置） ---
st.markdown("---")
tab1, tab2 = st.tabs(["🔱 調練履歴", "🔱 RPM計算機"])

with tab1:
    sheet = connect_to_sheet()
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            st.dataframe(df.tail(10), use_container_width=True)

with tab2:
    col_w, col_r = st.columns(2)
    with col_w:
        weight = st.number_input("重量 (kg)", value=100.0, step=2.5, key="rpm_w")
    with col_r:
        reps = st.number_input("レップ数", value=1, step=1, key="rpm_r")
    
    estimated_1rm = weight * (1 + reps/30)
    st.metric(label="推定1RM (Epley)", value=f"{estimated_1rm:.2f} kg")
    
    if st.button("🔱 推定1RMを記録"):
        sheet = connect_to_sheet()
        if sheet:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            sheet.append_row([now, "1RM記録", f"{weight}kg x {reps}", "-", f"推定1RM: {estimated_1rm:.2f}kg"])
            st.success(f"🔱 記録完了。目標 103.5kg まで残り {max(0, 103.5 - estimated_1rm):.2f}kg だ。")
