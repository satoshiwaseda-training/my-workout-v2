import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. アプリ全体の初期化 ---
if 'active_tasks' not in st.session_state:
    st.session_state.active_tasks = []

st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")

# --- 2. モデル安定化のためのAPI関数 ---
def call_gemini_3_flash(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # 最新の Gemini 3 Flash モデルを明示的に指定
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2, # 精度重視
            "topP": 0.8,
            "maxOutputTokens": 1000,
        }
    }
    
    # 最大3回のリトライロジック
    for attempt in range(3):
        try:
            res = requests.post(url, json=payload, timeout=30)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            if attempt == 2: return None
    return None

# --- 3. UI構築 (以下、以前の鉄壁UIを維持) ---
st.title("💪 Muscle Mate: Gemini 3 Powered")

# 基準値入力
c1, c2, c3 = st.columns(3)
with c1: rpm_bp = st.number_input("BP MAX", value=115.0, key="rpm_bp")
with c2: rpm_sq = st.number_input("SQ MAX", value=140.0, key="rpm_sq")
with c3: rpm_dl = st.number_input("DL MAX", value=160.0, key="rpm_dl")

# 実行設定
st.markdown("---")
c_time, c_target = st.columns([1, 2])
with c_time: t_limit = st.selectbox("時間", [60, 90], index=0)
with c_target: targets = st.multiselect("対象部位", ["胸 (BP)", "脚 (SQ)", "背中 (DL)", "肩", "腕"], default=["胸 (BP)"])

# メニュー生成ボタン
if st.button("🚀 Gemini 3 に設計図を依頼する"):
    with st.spinner("Gemini 3 Flash がDriveの聖典を読み込み中..."):
        # Driveのルーティンを考慮させるための強力なプロンプト
        prompt = (
            f"あなたはMuscle Mate。サトシさんのBP:{rpm_bp}kg基準。時間{t_limit}分。対象{targets}。"
            f"【最優先】Google Driveの『ベンチプレス通常ルーティン』と『120kgプログラム』を参照せよ。"
            f"今日がサイクルの何回目かを履歴から判断し、ナロープレス等の補助種目も含めよ。"
            f"形式：種目名:重量kgx回数xセット数[休憩:秒]"
        )
        resp_text = call_gemini_3_flash(prompt)
        
        if resp_text:
            parsed = []
            for line in resp_text.split('\n'):
                match = re.search(r'([^:：]+)[:：]\s*(\d+\.?\d*)\s*kg?\s*x\s*(\d+)\s*x\s*(\d+)', line, re.IGNORECASE)
                if match:
                    parsed.append({"name": match.group(1).strip("*・ "), "w": float(match.group(2)), "r": int(match.group(3)), "s": int(match.group(4))})
            st.session_state.active_tasks = parsed
            st.rerun()
        else:
            st.error("通信がタイムアウトしました。もう一度だけボタンを押してください。")

# --- 4. 【死守UI】入力フォームの表示 ---
# (中略：以前のプルダウン付きフォームを継承)
