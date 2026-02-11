import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re
import time

# --- 1. 初期化 & 聖典データ ---
if 'active_tasks' not in st.session_state:
    st.session_state.active_tasks = []

# AIが落ちた時のためのバックアップメニュー (サトシさん専用)
BACKUP_MENU = {
    "胸 (BP)": [{"name": "ベンチプレス", "w": 85.0, "r": 5, "s": 3}, {"name": "ディップス", "w": 0.0, "r": 10, "s": 3}],
    "脚 (SQ)": [{"name": "スクワット", "w": 100.0, "r": 5, "s": 3}],
    "背中 (DL)": [{"name": "デッドリフト", "w": 120.0, "r": 5, "s": 1}],
    "肩": [{"name": "ショルダープレス", "w": 20.0, "r": 10, "s": 3}],
    "腕": [{"name": "ナロープレス", "w": 60.0, "r": 10, "s": 3}]
}

st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")

# --- 2. 超回復型APIエンジン ---
def fetch_menu_persistent(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # 最新かつ安定性の高いエンドポイントを使用
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    for i in range(3): # 3回のリトライ
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=25)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text']
            time.sleep(1) # 短い休憩を挟んで再起
        except:
            continue
    return None

# --- 3. UI構築 ---
st.title("💪 Muscle Mate: Absolute Resilience")

# 1RM基準値
c1, c2, c3 = st.columns(3)
with c1: rpm_bp = st.number_input("BP MAX", value=115.0, key="rpm_bp")
with c2: rpm_sq = st.number_input("SQ MAX", value=140.0, key="rpm_sq")
with c3: rpm_dl = st.number_input("DL MAX", value=160.0, key="rpm_dl")

st.markdown("---")
targets = st.multiselect("対象部位", list(BACKUP_MENU.keys()), default=["胸 (BP)"])

# メニュー生成ボタン
if st.button("🚀 鉄壁の通信でメニューを生成"):
    with st.spinner("AIラインを確保中..."):
        prompt = f"Muscle MateとしてBP:{rpm_bp}kg基準で{targets}のメニューを提案せよ。形式：種目名:重量kgx回数xセット数"
        resp_text = fetch_menu_persistent(prompt)
        
        if resp_text:
            parsed = []
            for line in resp_text.split('\n'):
                match = re.search(r'([^:：]+)[:：]\s*(\d+\.?\d*)\s*kg?\s*x\s*(\d+)\s*x\s*(\d+)', line, re.IGNORECASE)
                if match:
                    parsed.append({"name": match.group(1).strip(), "w": float(match.group(2)), "r": int(match.group(3)), "s": int(match.group(4))})
            if parsed:
                st.session_state.active_tasks = parsed
                st.rerun()
        
        # AIが全滅した場合のバックアップ発動
        st.warning("AIが混雑中のため、サトシさんのバックアッププランをロードしました！")
        backup = []
        for t in targets:
            backup.extend(BACKUP_MENU.get(t, []))
        st.session_state.active_tasks = backup
        st.rerun()

# --- 4. 入力フォーム & 保存 (前回同様) ---
# ... (中略) ...
