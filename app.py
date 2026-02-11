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
    .error-box { background: #fff5f5; border: 2px solid #ff4b2b; padding: 15px; border-radius: 10px; color: #cc0000; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("💪 Muscle Mate: Absolute Sync")

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
with c1: rpm_bp = st.number_input("BP MAX", value=115.0, key="rpm_bp")
with c2: rpm_sq = st.number_input("SQ MAX", value=140.0, key="rpm_sq")
with c3: rpm_dl = st.number_input("DL MAX", value=160.0, key="rpm_dl")

# --- 4. 設定 ---
st.markdown("---")
c_time, c_target = st.columns([1, 2])
with c_time: t_limit = st.selectbox("時間", [60, 90], index=0)
with c_target: targets = st.multiselect("対象部位", ["胸 (BP)", "脚 (SQ)", "背中 (DL)", "肩", "腕"], default=["胸 (BP)"])

# --- 5. メニュー生成ロジック ---
if st.button("🚀 プログラムからメニューを生成"):
    with st.spinner("サトシさんのために計算中..."):
        try:
            api_key = st.secrets["GOOGLE_API_KEY"].strip()
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
            
            system = (
                f"あなたはMuscle Mate。サトシさんのBP:{rpm_bp}kg基準。時間{t_limit}分。"
                f"ディップスを含む3種目を提案せよ。重量は一般的で安全なRPE8基準。"
                f"【厳守】以下の形式のみで出力せよ。説明は不要。\n"
                f"種目名:重量kgx回数xセット数[休憩:秒]"
            )
            payload = {"contents": [{"parts": [{"text": f"{system}\n\n対象部位{targets}。設計図を出せ。"}]}]}
            res = requests.post(url, json=payload, timeout=15)
            
            if res.status_code == 200:
                resp_text = res.json()['candidates'][0]['content']['parts'][0]['text']
                st.session_state['ai_resp_display'] = resp_text
                
                parsed = []
                # 【改善】パースロジックをよりシンプルかつ強力に
                lines = resp_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line or ":" not in line: continue
                    
                    # 種目名 : 数値 kg x 数値 x 数値 [休憩:数値] を抽出
                    match = re.search(r'([^:：]+)[:：]\s*(\d+\.?\d*)\s*kg?\s*x\s*(\d+)\s*x\s*(\d+)', line, re.IGNORECASE)
                    if match:
                        rest_match = re.search(r'(\d+)', line.split(']')[-2] if ']' in line else line.split('休憩')[-1])
                        parsed.append({
                            "name": match.group(1).strip("*・ "),
                            "w": float(match.group(2)),
                            "r": int(match.group(3)),
                            "s": int(match.group(4)),
                            "rest": int(rest_match.group(1)) if rest_match else 90
                        })
                
                if parsed:
                    st.session_state['active_tasks'] = parsed
                    st.rerun()
                else:
                    # 【改善】生成失敗時の提案
                    st.session_state['active_tasks'] = [] # 空にする
                    st.error("AIの回答形式を読み取れませんでした。AIの回答を元に手動で調整が必要です。")
            else:
                st.error("通信エラーが発生しました。")
        except Exception as e:
            st.error(f"システムエラー: {e}")

# --- 6. 【死守UI】記録欄の表示 ---
if st.session_state['active_tasks'] is not None:
    if not st.session_state['active_tasks']:
        st.markdown(f'<div class="error-box">⚠️ AIは以下のように提案しましたが、自動入力に失敗しました。この内容を参考に手動で入力してください：<br><br>{st.session_state["ai_resp_display"]}</div>', unsafe_allow_html=True)
    else:
        st.info(f"📋 AI提案値との同期完了:\n{st.session_state['ai_resp_display']}")
    
    with st.form("ultimate_record_form"):
        all_logs = []
        total_vol = 0
        tasks = st.session_state['active_tasks'] if st.session_state['active_tasks'] else [{"name": "手動追加種目", "w": 0.0, "r": 0, "s": 3, "rest": 90}]
        
        for i, task in enumerate(tasks):
            st.markdown(f'<div class="workout-card">### 🏋️ {task["name"]} (推奨: {task["w"]}kg)</div>', unsafe_allow_html=True)
            for s_num in range(1, task['s'] + 1):
                c_label, c_w, c_r = st.columns([1, 2, 2])
                with c_label: st.write(f"Set {s_num}")
                # AI提案値をデフォルト値に確実にセット
                w = st.number_input(f"重量(kg)", value=task['w'], key=f"w_{i}_{s_num}", step=0.5)
                r = st.number_input(f"回数", value=float(task['r']), key=f"r_{i}_{s_num}", step=1.0)
                if w > 0 or r > 0:
                    total_vol += w * r
                    all_logs.append(f"{task['name']}(S{s_num}):{w}kgx{int(r)}")
            st.markdown("---")

        if st.form_submit_button("🔥 実績をGoogle Driveへ保存"):
            if sheet and all_logs:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                sheet.append_row([now, f"{t_limit}min session", ", ".join(targets), ", ".join(all_logs), f"Vol:{total_vol}kg"])
                st.balloons()
                st.success("実績を保存しました！")
                st.session_state['active_tasks'] = None
                st.rerun()
