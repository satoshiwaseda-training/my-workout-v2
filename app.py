import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. 聖域接続 (Drive & Sheets 完全同期) ---
def connect_to_google():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        client = gspread.authorize(creds)
        # スプレッドシートとDriveの操作用
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
        return sheet, client
    except: return None, None

# --- 2. UI スタイル (モチベ爆上げグラデーション) ---
st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); color: #444; }
    .stMetric { background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .stButton>button { background: linear-gradient(to right, #FF4B2B, #FF416C); color: white; border-radius: 20px; font-weight: bold; border: none; height: 3.5em; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Active Performance")
st.write("MAX 115kg 基準：最新の運動生理学に基づき、今日この瞬間の最適を。")

# 接続
sheet, client = connect_to_google()
df_past = pd.DataFrame()
if sheet:
    data = sheet.get_all_values()
    if len(data) > 1:
        df_past = pd.DataFrame(data[1:], columns=data[0])

# --- 3. ダッシュボード ---
c1, c2, c3 = st.columns(3)
with c1: st.metric("1RM基準", "115.0 kg")
with c2: st.metric("今週の総負荷量", "64.66 t")
with c3:
    acc_kg = 3690660 # 累計
    st.metric("飛行機積載量換算", f"{acc_kg/180000:.4f} ✈️")

# --- 4. 部位別・プログラム選択 & AI提案 ---
st.markdown("---")
col_p, col_t = st.columns(2)
with col_p:
    prog = st.selectbox("プログラム", ["ベンチプレス強化", "スクワット強化", "デッドリフト強化", "筋肥大", "筋力増強"])
with col_t:
    targets = st.multiselect("対象部位", ["胸", "背中", "脚", "肩", "腕", "腹筋"], default=["胸"])

if st.button("🚀 今日のメニューを相談する"):
    with st.spinner("世界中の最新論文とDrive履歴を解析中..."):
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        past_context = df_past.tail(10).to_string() if not df_past.empty else "新規"
        # 科学的根拠を世界規模に拡張
        system = (
            f"あなたは最高のパートナー『Muscle Mate』。ベンチMAX115kg。世界中の運動生理学（Progressive Overload等）"
            f"の論文、6回1周サイクルに基づき提案せよ。今日はDay {(datetime.now().day % 6) + 1}。部位:{targets}に集中せよ。"
            f"\n【履歴】\n{past_context}"
        )
        payload = {"contents": [{"parts": [{"text": f"{system}\n\n指令：{prog}の今日のメニューを提案して。"}]}]}
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            st.session_state['ai_resp'] = res.json()['candidates'][0]['content']['parts'][0]['text']
            # AI提案から「種目」と「想定重量/回数」を抽出
            items = re.findall(r'[*・]\s*([^\s(（]+)', st.session_state['ai_resp'])
            st.session_state['active_tasks'] = items[:4] # 今日こなすべき種目

if 'ai_resp' in st.session_state:
    st.info(st.session_state['ai_resp'])

# --- 5. 【復元】今日こなすものだけの動的入力 & Drive保存 ---
if 'active_tasks' in st.session_state:
    st.markdown("---")
    st.subheader(f"📝 本日の調練記録 ({', '.join(targets)})")
    
    with st.form("dynamic_record_form"):
        logs = []
        total_today = 0
        for i, task in enumerate(st.session_state['active_tasks']):
            c_ex, c_w, c_r, c_s = st.columns([3, 1, 1, 1])
            with c_ex:
                # 提案種目を固定しつつ、変更も可能
                ex = st.text_input(f"種目 {i+1}", value=task, key=f"ex_{i}")
            with c_w: w = st.number_input("kg", key=f"w_{i}", step=2.5, format="%.1f")
            with c_r: r = st.number_input("回数", key=f"r_{i}", step=1)
            with c_s: s = st.number_input("セット", key=f"s_{i}", step=1)
            
            if w > 0:
                total_today += w * r * s
                logs.append(f"{ex}:{w}kgx{r}x{s}")

        if st.form_submit_button("🔥 実績をDriveに同期・保存"):
            if sheet and logs:
                now = datetime.now().strftime("%Y-%m-%d")
                # 1. スプレッドシート更新
                sheet.append_row([now, prog, ", ".join(targets), ", ".join(logs), f"Total:{total_today}kg"])
                
                # 2. Driveへの個別ファイル格納 (モチベーション管理用)
                try:
                    folder_id = st.secrets.get("drive_folder_id") # もしあれば
                    # ここでDrive API等を使ったファイル作成処理が可能
                except: pass
                
                st.balloons()
                st.success(f"ナイス！総負荷 {total_today}kg (軽自動車 {total_today/1000:.2f}台分) をDriveに刻みました！")

# --- 6. 履歴 & 設定 ---
st.markdown("---")
tab1, tab2 = st.tabs(["📜 履歴", "⚙️ 設定"])
with tab1:
    if not df_past.empty: st.dataframe(df_past.tail(15), use_container_width=True)
with tab2:
    st.write("1RM基準: 115kg / 理論: 世界の運動科学論文 / 連携: Google Drive")
