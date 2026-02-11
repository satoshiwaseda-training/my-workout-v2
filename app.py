import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import re

# --- 1. 部位別・聖典バックアップメニュー ---
# AIが落ちても、サトシさんの基準値から自動計算
def get_fallback_menu(targets, bp, sq, dl):
    menu = []
    for t in targets:
        if "胸" in t:
            menu.append({"name": "ベンチプレス", "w": bp * 0.75, "r": 5, "s": 3})
            menu.append({"name": "ディップス", "w": 0.0, "r": 10, "s": 3})
        elif "脚" in t:
            menu.append({"name": "スクワット", "w": sq * 0.75, "r": 5, "s": 3})
            menu.append({"name": "レッグプレス", "w": 120.0, "r": 10, "s": 3})
        elif "背中" in t:
            menu.append({"name": "デッドリフト", "w": dl * 0.75, "r": 5, "s": 1})
            menu.append({"name": "懸垂", "w": 0.0, "r": 8, "s": 3})
    return menu

# --- 2. 初期化 ---
if 'active_tasks' not in st.session_state:
    st.session_state.active_tasks = []

st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")

st.title("💪 Muscle Mate: Intelligent Logic Sync")

# --- 3. 基準値入力 ---
c1, c2, c3 = st.columns(3)
with c1: rpm_bp = st.number_input("BP MAX", value=115.0)
with c2: rpm_sq = st.number_input("SQ MAX", value=140.0)
with c3: rpm_dl = st.number_input("DL MAX", value=160.0)

st.markdown("---")
# 部位選択（プルダウン形式で種目も連動）
targets = st.multiselect("対象部位", ["胸 (BP)", "脚 (SQ)", "背中 (DL)", "肩", "腕"], default=["脚 (SQ)"])

# --- 4. メニュー生成 (AI + 鉄壁のロジック) ---
if st.button("🚀 部位に合わせた設計図を生成"):
    with st.spinner("サトシさんの聖典を確認中..."):
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        # 強力な指令
        prompt = (f"Muscle Mateとして、サトシさんの部位:{targets}に最適なメニューを提案せ do。 "
                  f"基準は BP:{rpm_bp}kg, SQ:{rpm_sq}kg, DL:{rpm_dl}kg。 "
                  f"形式：種目名:重量kgx回数xセット数")
        
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
            if res.status_code == 200:
                resp_text = res.json()['candidates'][0]['content']['parts'][0]['text']
                parsed = []
                for line in resp_text.split('\n'):
                    match = re.search(r'([^:：]+)[:：]\s*(\d+\.?\d*)\s*kg?\s*x\s*(\d+)\s*x\s*(\d+)', line, re.IGNORECASE)
                    if match:
                        parsed.append({"name": match.group(1).strip(), "w": float(match.group(2)), "r": int(match.group(3)), "s": int(match.group(4))})
                if parsed:
                    st.session_state.active_tasks = parsed
                    st.rerun()
        except:
            pass
        
        # AIが失敗、もしくは部位が矛盾した際の鉄壁バックアップ
        st.warning(f"{targets}のバックアッププランをロードしました。")
        st.session_state.active_tasks = get_fallback_menu(targets, rpm_bp, rpm_sq, rpm_dl)
        st.rerun()

# --- 5. 入力フォーム ---
if st.session_state.active_tasks:
    # (以下、以前の種目名選択・重量・回数入力UIを表示)
    pass
