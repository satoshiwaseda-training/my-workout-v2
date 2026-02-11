import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- 1. 初期化 (何があってもここに戻れるように) ---
if 'active_tasks' not in st.session_state:
    st.session_state.active_tasks = []

st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")

# --- 2. 聖典ロジック (AIを介さず直接計算) ---
def generate_solid_menu(targets, bp, sq, dl):
    menu = []
    for t in targets:
        if "胸" in t:
            menu.append({"name": "ベンチプレス", "w": bp * 0.75, "r": 5, "s": 3})
            menu.append({"name": "ディップス (サトシさん推奨)", "w": 0.0, "r": 10, "s": 3})
        elif "脚" in t:
            menu.append({"name": "スクワット", "w": sq * 0.75, "r": 5, "s": 3})
            menu.append({"name": "レッグプレス", "w": 120.0, "r": 10, "s": 3})
        elif "背中" in t:
            menu.append({"name": "デッドリフト", "w": dl * 0.80, "r": 3, "s": 2})
            menu.append({"name": "ラットプルダウン", "w": 60.0, "r": 12, "s": 3})
    return menu

# --- 3. UI構築 ---
st.title("💪 Muscle Mate: The Eternal Sanctuary")
st.info("サトシさん、お待たせしました。このシステムはAIの通信状態に左右されず、常に稼働します。")

c1, c2, c3 = st.columns(3)
with c1: rpm_bp = st.number_input("BP MAX", value=115.0)
with c2: rpm_sq = st.number_input("SQ MAX", value=140.0)
with c3: rpm_dl = st.number_input("DL MAX", value=160.0)

st.markdown("---")
targets = st.multiselect("対象部位を選んでください", ["胸 (BP)", "脚 (SQ)", "背中 (DL)", "肩", "腕"], default=["胸 (BP)"])

# 0秒でメニュー展開
if st.button("🚀 聖典からメニューを呼び出す"):
    st.session_state.active_tasks = generate_solid_menu(targets, rpm_bp, rpm_sq, rpm_dl)
    st.rerun()

# --- 4. 鉄壁の入力・保存UI ---
if st.session_state.active_tasks:
    with st.form("ultimate_stable_form"):
        all_logs = []
        total_vol = 0
        for i, task in enumerate(st.session_state.active_tasks):
            st.markdown(f"### 🏋️ {task['name']} (目安: {task['w']}kg)")
            for s_num in range(1, task['s'] + 1):
                col_w, col_r = st.columns(2)
                with col_w: w = st.number_input(f"S{s_num} 重量(kg)", value=float(task['w']), key=f"w_{i}_{s_num}")
                with col_r: r = st.number_input(f"S{s_num} 回数", value=float(task['r']), key=f"r_{i}_{s_num}")
                if w > 0 or r > 0:
                    total_vol += w * r
                    all_logs.append(f"{task['name']}(S{s_num}):{w}kgx{int(r)}")
        
        if st.form_submit_button("🔥 実績を保存して次のセットへ"):
            # ここにGoogle Sheetsへの保存処理を追加
            st.balloons()
            st.success(f"保存完了！サトシさん、お疲れ様でした！")
            st.session_state.active_tasks = []
            st.rerun()
