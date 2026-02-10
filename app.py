import streamlit as st
import requests
import json
import gspread
from google.oauth2.service_account import Credentials
import re
from datetime import datetime

# --- 1. スプレッドシート同期 ---
def save_to_sheets(rows):
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
        sheet.append_rows(rows)
        return True
    except Exception as e:
        st.error(f"Sheet Sync Error: {e}")
        return False

# --- 2. デザイン ---
st.set_page_config(page_title="GOD-MODE AI ANALYST", page_icon="🔱", layout="wide")
st.markdown("""<style>
    .stApp { background: #0e1117; color: #ffffff; }
    .record-card { background: #1a1c23; padding: 25px; border-radius: 15px; border-left: 5px solid #007aff; margin-bottom: 15px; }
    .ai-thought { background: #262730; border-left: 5px solid #007aff; padding: 15px; font-style: italic; color: #d1d1d1; margin-bottom: 20px; }
    h1, h2, h3 { color: #007aff !important; }
</style>""", unsafe_allow_html=True)

# --- 3. セッション初期化 ---
for key, val in {
    "menu_data": [], "routine_count": 0, "ai_thought": "",
    "bp_max": 103.5, "sq_max": 168.8, "dl_max": 150.0,
    "knowledge_base": "【2月実績】SQ:168.8, BP:103.5 / Drive文献：ストレングス理論、過去の全ログ",
    "custom_constraints": "脚の日は腹筋必須。ベンチプレスは過去のルール遵守。"
}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 4. 404を物理的に回避する「マルチエンドポイント」生成 ---
def generate_menu_final_attempt(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    
    # 試行するURLリスト（AI Studio用とVertex AI用の両方をカバー）
    urls = [
        # パターンA: AI Studio 標準 (v1)
        f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={api_key}",
        # パターンB: AI Studio 最新 (v1beta)
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
        # パターンC: プロジェクトIDを介さないグローバル形式
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    ]
    
    payload = {"contents": [{"parts": [{"text": f"分析根拠を述べてからメニューを作れ。文献・履歴を重視せよ。\n\n{prompt}"}]}]}
    headers = {'Content-Type': 'application/json'}

    errors = []
    for url in urls:
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                errors.append(f"URL失敗 ({url.split('/')[3]}): {res.status_code}")
        except:
            continue
            
    raise Exception(f"全エンドポイントが拒絶。詳細はSecretsのキーを確認: {', '.join(errors)}")

def parse_menu(text):
    items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)?', text)
    return [{"name": n, "w_def": float(re.search(r'\d+\.?\d*', w).group()) if re.search(r'\d+', w) else 0.0, 
             "sets": int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 3, 
             "r_def": int(re.search(r'\d+', r).group()) if r and re.search(r'\d+', r) else 10} for n, w, s, r in items]

# --- 5. メインUI ---
st.title("🔱 GOD-MODE: INTELLIGENT TRAINING")

mode = st.selectbox("ターゲット", ["ベンチプレス", "スクワット", "デッドリフト"])

if st.button("文献・履歴を完全同期して生成 (FORCE CONNECT)"):
    step = (st.session_state.routine_count % 6) + 1
    target_max = st.session_state.bp_max if mode=="ベンチプレス" else st.session_state.sq_max
    target_w = round(target_max * [0.6, 0.7, 0.7, 0.75, 0.8, 0.85][step-1], 1)

    prompt = f"Step {step}/6 メニュー。知識:{st.session_state.knowledge_base}。履歴:{st.session_state.custom_constraints}。メイン:『{mode}』【{target_w}kg】({step + 2}セット) 5回。形式:『種目名』 【重量kg】 (セット数) 回数"
    
    with st.spinner("🔱 通信経路を確保中..."):
        try:
            raw_text = generate_menu_final_attempt(prompt)
            st.session_state.ai_thought = raw_text.split('『')[0]
            st.session_state.menu_data = parse_menu(raw_text)
        except Exception as e:
            st.error(f"AI通信エラー: {e}")

if st.session_state.ai_thought:
    st.markdown("### 🔱 分析根拠")
    st.markdown(f'<div class="ai-thought">{st.session_state.ai_thought}</div>', unsafe_allow_html=True)

# --- 6. 記録・表示 (中略。前回の安定版と同じロジック) ---
if st.session_state.menu_data:
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        st.subheader(item.get('name', '種目'))
        c1, c2, c3 = st.columns(3)
        w = c1.number_input("kg", 0.0, 500.0, float(item.get('w_def', 0.0)), key=f"w_{idx}")
        r = c2.number_input("回", 0, 100, int(item.get('r_def', 10)), key=f"r_{idx}")
        s = c3.number_input("セット", 1, 15, int(item.get('sets', 3)), key=f"s_{idx}")
        current_logs.append({"name": item.get('name'), "w": w, "r": r, "s": s})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Driveへ同期"):
        rows = [[datetime.now().strftime('%Y-%m-%d %H:%M'), l['name'], l['w'], l['r'], l['s']] for l in current_logs]
        if save_to_sheets(rows):
            st.balloons(); st.session_state.routine_count += 1; st.session_state.menu_data = []; st.rerun()
