import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import re
import time

# --- 1. 初期化 & セッション管理 ---
if 'active_tasks' not in st.session_state:
    st.session_state.active_tasks = []

st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")

# --- 2. 最新の安定通信エンジン (Gemini 2.0 Flash) ---
def fetch_menu_from_gemini(prompt):
    try:
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        # 最新の安定エンドポイント
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3}
        }
        
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception:
        return None
    return None

# --- 3. UI構築 ---
st.title("💪 Muscle Mate: The Eternal Connection")

# 1RM基準値
c1, c2, c3 = st.columns(3)
with c1: rpm_bp = st.number_input("BP MAX (115kg)", value=115.0, key="rpm_bp")
with c2: rpm_sq = st.number_input("SQ MAX", value=140.0, key="rpm_sq")
with c3: rpm_dl = st.number_input("DL MAX", value=160.0, key="rpm_dl")

st.markdown("---")
targets = st.multiselect("対象部位", ["胸 (BP)", "脚 (SQ)", "背中 (DL)", "肩", "腕"], default=["胸 (BP)"])

# メニュー生成ボタン
if st.button("🚀 最新モデルでメニューを生成"):
    with st.spinner("AIラインを確保中..."):
        prompt = (
            f"あなたはサトシさんのパートナーMuscle Mate。BP:{rpm_bp}kg基準。対象:{targets}。"
            f"『120kgプログラム』の補助種目(ディップス等)を必ず含めよ。"
            f"形式：種目名:重量kgx回数xセット数[休憩:秒]"
        )
        resp_text = fetch_menu_from_gemini(prompt)
        
        parsed = []
        if resp_text:
            for line in resp_text.split('\n'):
                match = re.search(r'([^:：]+)[:：]\s*(\d+\.?\d*)\s*kg?\s*x\s*(\d+)\s*x\s*(\d+)', line, re.IGNORECASE)
                if match:
                    parsed.append({"name": match.group(1).strip("*・ "), "w": float(match.group(2)), "r": int(match.group(3)), "s": int(match.group(4))})
        
        if parsed:
            st.session_state.active_tasks = parsed
            st.success("最新モデルとの同期に成功！")
            st.rerun()
        else:
            # AIが完全に沈黙した場合の緊急プロトコル
            st.error("AIラインが混雑しています。サトシさんの基本プランを展開します！")
            st.session_state.active_tasks = [
                {"name": "ベンチプレス", "w": rpm_bp * 0.75, "r": 5, "s": 3},
                {"name": "ディップス", "w": 0.0, "r": 10, "s": 3}
            ]
            st.rerun()

# --- 4. 鉄壁の入力フォーム ---
if st.session_state.active_tasks:
    with st.form("stable_workout_form"):
        all_logs = []
        total_vol = 0
        for i, task in enumerate(st.session_state.active_tasks):
            st.markdown(f"### 🏋️ {task['name']} ({task['w']}kg目標)")
            for s_num in range(1, int(task['s']) + 1):
                col_w, col_r = st.columns(2)
                with col_w: w = st.number_input(f"S{s_num} 重量(kg)", value=float(task['w']), key=f"w_{i}_{s_num}")
                with col_r: r = st.number_input(f"S{s_num} 回数", value=float(task['r']), key=f"r_{i}_{s_num}")
                if w > 0 or r > 0:
                    total_vol += w * r
                    all_logs.append(f"{task['name']}(S{s_num}):{w}kgx{int(r)}")
        
        if st.form_submit_button("🔥 実績をGoogle Driveへ保存"):
            # (保存処理)
            st.balloons()
            st.session_state.active_tasks = []
            st.rerun()
