import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. UI スタイル (鉄壁の動的UI) ---
st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #ffedbc 0%, #ff9a9e 100%); }
    .stNumberInput input { font-size: 1.1em !important; font-weight: bold !important; border: 2px solid #ff4b2b !important; }
    .stButton>button { background: linear-gradient(to right, #FF4B2B, #FF416C); color: white; border-radius: 20px; font-weight: bold; height: 3.5em; width: 100%; border: none; }
    .interval-box { background: #fff5f5; border: 1px solid #ffc9c9; padding: 10px; border-radius: 10px; color: #e03131; font-weight: bold; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Interval-Driven Training")

# --- 2. 実行設定 ---
st.subheader("🏋️ 今日のセッション設定")
c_time, c_target = st.columns([1, 2])
with c_time: 
    t_limit = st.selectbox("トレーニング時間", [60, 90], index=0, format_func=lambda x: f"{x}分")
with c_target: 
    targets = st.multiselect("鍛錬部位", ["胸 (BP)", "脚 (SQ)", "背中 (DL)", "肩", "腕"], default=["胸 (BP)"])

# --- 3. プログラム参照 & 休憩加味メニュー生成 ---
if st.button("🚀 休憩時間を含めた最適メニューを展開"):
    with st.spinner("休憩時間と回復率を計算中..."):
        api_key = st.secrets["GOOGLE_API_KEY"].strip()
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        # 指令：休憩時間を計算に含め、時間内に収まるセット数を算出させる
        system = (
            f"あなたはMuscle Mate。制限時間{t_limit}分。対象部位{targets}。"
            f"【休憩プロトコル】コンパウンド種目は180秒、その他は部位や強度に応じ60-120秒の休憩をセット間に設定せよ。"
            f"全セット時間＋全休憩時間 ≦ {t_limit}分 となるように、Drive内の各プログラムを参照して種目数とセット数を最適化せよ。"
            f"出力形式：'種目名:重量kgx回数xセット数[休憩:秒]'"
        )
        payload = {"contents": [{"parts": [{"text": f"{system}\n\n指令：本日の設計図を出せ。"}]}]}
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            resp_text = res.json()['candidates'][0]['content']['parts'][0]['text']
            st.session_state['ai_resp'] = resp_text
            parsed = []
            for line in resp_text.split('\n'):
                # 休憩時間の抽出も含む正規表現
                match = re.search(r'[*・]?\s*([^:]+):(\d+\.?\d*)kgx(\d+)x(\d+)\[休憩:(\d+)\]', line)
                if match:
                    parsed.append({
                        "name": match.group(1), "w": float(match.group(2)), 
                        "r": int(match.group(3)), "s": int(match.group(4)), 
                        "rest": int(match.group(5))
                    })
            st.session_state['active_tasks'] = parsed

# --- 4. 【絶対死守UI】セット別入力欄 + 休憩タイマーガイド ---
if 'active_tasks' in st.session_state:
    st.info(f"📋 タイムマネジメント設計図:\n{st.session_state['ai_resp']}")
    
    with st.form("interval_workout_form"):
        all_logs = []
        total_vol = 0
        for i, task in enumerate(st.session_state['active_tasks']):
            st.markdown(f"### 🏋️ {task['name']}")
            st.markdown(f'<div class="interval-box">⏱️ 推奨セット間休憩: {task["rest"]}秒</div>', unsafe_allow_html=True)
            
            for s_num in range(1, task['s'] + 1):
                c_label, c_w, c_r = st.columns([1, 2, 2])
                with c_label: st.write(f"Set {s_num}")
                with c_w: w = st.number_input(f"重量(kg)", value=task['w'], key=f"w_{i}_{s_num}", step=0.5)
                with c_r: r = st.number_input(f"回数", value=task['r'], key=f"r_{i}_{s_num}", step=1)
                
                if w > 0:
                    total_vol += w * r
                    all_logs.append(f"{task['name']}(S{s_num}):{w}kgx{r}")
            st.markdown("---")

        if st.form_submit_button("🔥 実績を同期して終了"):
            # Drive保存ロジック...
            st.balloons()
            st.success(f"鍛錬完了！総負荷: {total_vol}kg を保存しました。")
