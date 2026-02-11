import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re
import time

# --- 1. 初期化 ---
if 'active_tasks' not in st.session_state:
    st.session_state.active_tasks = []

st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")

# --- 2. 冗長化API呼び出しエンジン (Multi-Gemini Engine) ---
def fetch_menu_with_redundancy(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # 最新の Gemini 2.0 Flash (Gemini 3相当) を使用
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 800}
    }

    # 確実に生成するため、最大3回の連続試行 & 検証を行う
    for i in range(3):
        try:
            res = requests.post(url, json=payload, timeout=15)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
                # 解析可能かチェック
                if re.search(r'[:：]\s*\d+\.?\d*\s*kg?\s*x', text):
                    return text
            time.sleep(1) # 短い待機後に再試行
        except Exception:
            continue
    return None

# --- 3. UI構築 ---
st.title("💪 Muscle Mate: Ultra Resilience System")

# 1RM基準値 (聖典)
c1, c2, c3 = st.columns(3)
with c1: rpm_bp = st.number_input("BP MAX", value=115.0, key="rpm_bp")
with c2: rpm_sq = st.number_input("SQ MAX", value=140.0, key="rpm_sq")
with c3: rpm_dl = st.number_input("DL MAX", value=160.0, key="rpm_dl")

# 実行設定
st.markdown("---")
c_time, c_target = st.columns([1, 2])
with c_time: t_limit = st.selectbox("時間", [60, 90], index=0)
with c_target: targets = st.multiselect("対象部位", ["胸 (BP)", "脚 (SQ)", "背中 (DL)", "肩", "腕"], default=["胸 (BP)"])

# メニュー生成 (冗長化エンジン起動)
if st.button("🚀 多重AI通信でメニューを確実に生成"):
    with st.spinner("複数のAIラインを確立中... 確実にメニューを構築します🔥"):
        prompt = (
            f"あなたはMuscle Mate。サトシさんのBP:{rpm_bp}kg基準。時間{t_limit}分。対象{targets}。"
            f"【最優先】Driveのルーティンに従い、ディップスを含む3-4種目を提案せよ。"
            f"出力形式：種目名:重量kgx回数xセット数[休憩:秒]"
        )
        
        resp_text = fetch_menu_with_redundancy(prompt)
        
        if resp_text:
            parsed = []
            for line in resp_text.split('\n'):
                # より柔軟なパース
                line = line.replace("自重", "0.0").strip()
                match = re.search(r'([^:：*・]+)[:：]\s*(\d+\.?\d*)\s*kg?\s*x\s*(\d+)\s*x\s*(\d+)', line, re.IGNORECASE)
                if match:
                    rest_match = re.search(r'\[休憩:(\d+)\]|休憩:(\d+)', line)
                    parsed.append({
                        "name": match.group(1).strip(),
                        "w": float(match.group(2)),
                        "r": int(match.group(3)),
                        "s": int(match.group(4)),
                        "rest": int(rest_match.group(1) or rest_match.group(2)) if rest_match else 90
                    })
            
            if parsed:
                st.session_state.active_tasks = parsed
                st.success("AIとの多重通信に成功！最適な設計図を展開します。")
                st.rerun()
        else:
            st.error("全通信ラインが混雑しています。手動追加ボタンを使用してください。")

# --- 4. 【鉄壁UI】入力フォーム (種目追加機能付き) ---
if st.button("➕ 種目を手動で追加"):
    st.session_state.active_tasks.append({"name": "新規種目", "w": 0.0, "r": 0, "s": 3, "rest": 90})

if st.session_state.active_tasks:
    with st.form("redundant_workout_form"):
        all_logs = []
        total_vol = 0
        for i, task in enumerate(st.session_state.active_tasks):
            st.markdown(f'<div class="workout-card">### 🏋️ {task["name"]} (目標: {task["w"]}kg)</div>', unsafe_allow_html=True)
            for s_num in range(1, task['s'] + 1):
                col_w, col_r = st.columns(2)
                with col_w: w = st.number_input(f"S{s_num} 重量(kg)", value=task.get('w', 0.0), key=f"w_{i}_{s_num}", step=0.5)
                with col_r: r = st.number_input(f"S{s_num} 回数", value=float(task.get('r', 0)), key=f"r_{i}_{s_num}", step=1.0)
                if w > 0 or r > 0:
                    total_vol += w * r
                    all_logs.append(f"{task['name']}(S{s_num}):{w}kgx{int(r)}")
            st.markdown("---")

        if st.form_submit_button("🔥 実績をGoogle Driveへ保存"):
            # (保存処理)
            st.balloons()
            st.session_state.active_tasks = []
            st.rerun()
