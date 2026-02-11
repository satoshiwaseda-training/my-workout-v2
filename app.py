import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. 初期化 ---
if 'active_tasks' not in st.session_state:
    st.session_state['active_tasks'] = None
if 'ai_resp_display' not in st.session_state:
    st.session_state['ai_resp_display'] = ""

st.set_page_config(page_title="Muscle Mate", page_icon="💪", layout="wide")
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #ffedbc 0%, #ff9a9e 100%); }
    .stNumberInput input { font-size: 1.1em !important; font-weight: bold !important; border: 2px solid #ff4b2b !important; }
    .stButton>button { background: linear-gradient(to right, #FF4B2B, #FF416C); color: white; border-radius: 20px; font-weight: bold; height: 3.5em; width: 100%; border: none; }
    .workout-card { background: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 15px; border-left: 10px solid #FF4B2B; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Precise Sync")

# --- 2. Google Sheets 接続 ---
def connect_to_google():
    try:
        s_acc = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(s_acc, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["spreadsheet_id"]).sheet1
    except: return None

sheet = connect_to_google()

# --- 3. 1RM基準値 ---
c1, c2, c3 = st.columns(3)
with c1: rpm_bp = st.number_input("BP MAX (115kg基準)", value=115.0, key="rpm_bp")
with c2: rpm_sq = st.number_input("SQ MAX", value=140.0, key="rpm_sq")
with c3: rpm_dl = st.number_input("DL MAX", value=160.0, key="rpm_dl")

# --- 4. 設定 ---
st.markdown("---")
c_time, c_target = st.columns([1, 2])
with c_time: t_limit = st.selectbox("時間", [60, 90], index=0)
with c_target: targets = st.multiselect("対象部位", ["胸 (BP)", "脚 (SQ)", "背中 (DL)", "肩", "腕"], default=["胸 (BP)"])

# --- 5. メニュー生成ロジック ---
if st.button("🚀 メニューを生成して入力欄を展開"):
    with st.spinner("AIが全種目を精密に計算中..."):
        try:
            api_key = st.secrets["GOOGLE_API_KEY"].strip()
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
            
            # 補助種目（ディップス、ナロー等）を含めるよう、かつ形式を厳守させる
            system = (
                f"あなたはMuscle Mate。サトシさんのBP:{rpm_bp}kg基準。時間{t_limit}分。"
                f"休憩時間を考慮し、ディップスを含む3-4種目を提案せよ。"
                f"【出力形式厳守】以下の形式以外は一切出力するな。説明も不要。\n"
                f"種目名:重量kgx回数xセット数[休憩:秒]\n"
                f"例: ディップス:0kgx10x3[休憩:90]"
            )
            payload = {"contents": [{"parts": [{"text": f"{system}\n\n対象部位{targets}。ディップスを必ず含めた設計図を出せ。"}]}]}
            res = requests.post(url, json=payload, timeout=15)
            
            if res.status_code == 200:
                resp_text = res.json()['candidates'][0]['content']['parts'][0]['text']
                st.session_state['ai_resp_display'] = resp_text
                
                parsed = []
                lines = resp_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    # 改良版正規表現: 記号を除去し、重量・回数・セットを確実に抜く
                    match = re.search(r'([^:：*・]+)[:：]\s*(\d+\.?\d*)\s*kg?\s*x\s*(\d+)\s*x\s*(\d+)', line, re.IGNORECASE)
                    if match:
                        rest_match = re.search(r'休憩[:：]\s*(\d+)|\[休憩:(\d+)\]', line)
                        rest_val = 90
                        if rest_match:
                            rest_val = int(rest_match.group(1) or rest_match.group(2))
                        
                        parsed.append({
                            "name": match.group(1).strip(),
                            "w": float(match.group(2)),
                            "r": int(match.group(3)),
                            "s": int(match.group(4)),
                            "rest": rest_val
                        })
                
                if parsed:
                    st.session_state['active_tasks'] = parsed
                    st.rerun()
                else:
                    st.error(f"解析エラー。AIの回答に数値が含まれていないようです。回答: {resp_text}")
            else:
                st.error("通信エラーが発生しました。")
        except Exception as e:
            st.error(f"エラー: {e}")

# --- 6. 記録欄の表示 ---
if st.session_state['active_tasks']:
    st.info(f"📋 生成された設計図:\n{st.session_state['ai_resp_display']}")
    
    with st.form("perfect_sync_form"):
        all_logs = []
        total_vol = 0
        for i, task in enumerate(st.session_state['active_tasks']):
            st.markdown(f'<div class="workout-card">### 🏋️ {task["name"]} (目標: {task["w"]}kg)</div>', unsafe_allow_html=True)
            for s_num in range(1, task['s'] + 1):
                c_label, c_w, c_r = st.columns([1, 2, 2])
                with c_label: st.write(f"Set {s_num}")
                w = st.number_input(f"重量(kg)", value=task['w'], key=f"w_{i}_{s_num}", step=0.5)
                r = st.number_input(f"回数", value=task['r'], key=f"r_{i}_{s_num}", step=1)
                if w > 0 or r > 0: # 自重の場合w=0もあり得る
                    total_vol += w * r
                    all_logs.append(f"{task['name']}(S{s_num}):{w}kgx{r}")
            st.markdown("---")

        if st.form_submit_button("🔥 実績をGoogle Driveへ保存"):
            if sheet and all_logs:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                sheet.append_row([now, f"{t_limit}min session", ", ".join(targets), ", ".join(all_logs), f"Vol:{total_vol}kg"])
                st.balloons()
                st.success(f"保存完了！")
                st.session_state['active_tasks'] = None
                st.rerun()
