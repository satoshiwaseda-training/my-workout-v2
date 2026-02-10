import streamlit as st
import requests
import json
import gspread
from google.oauth2.service_account import Credentials
import re
from datetime import datetime

# --- 1. 同期設定 ---
def save_to_sheets(rows):
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
        sheet.append_rows(rows)
        return True
    except Exception as e:
        st.error(f"Sheet Error: {e}"); return False

# --- 2. デザイン ---
st.set_page_config(page_title="GOD-MODE AI ANALYST", page_icon="🔱", layout="wide")
st.markdown("<style>.stApp { background: #0e1117; color: white; } .record-card { background: #1a1c23; padding: 25px; border-radius: 15px; border-left: 5px solid #007aff; margin-bottom: 15px; }</style>", unsafe_allow_html=True)

# --- 3. セッション初期化 ---
for k, v in {
    "menu_data": [], "routine_count": 0, "ai_thought": "", 
    "bp_max": 103.5, "sq_max": 168.8,
    "knowledge_base": "【2026年実績】SQ:168.8, BP:103.5 / Drive文献：ストレングス理論、周期性トレーニング、過去のベンチプレス強度設定ログ",
    "custom_constraints": "脚の日は腹筋必須。ベンチプレスは過去の強度ルール（前回比・セット法）を完全遵守すること。"
}.items():
    if k not in st.session_state: st.session_state[k] = v

# --- 4. 究極のAI通信エンジン（404を物理的に回避） ---
def call_gemini_api_direct(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # 404を回避するための「安定版 v1」かつ「models/」プレフィックス付きURL
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{
                "text": f"あなたは最強のAIアナリストGOD-MODEです。以下の文献・履歴を分析し、最適なメニューを生成せよ。回答冒頭には必ず『🔱分析根拠』を詳しく記述せよ。\n\n指示：{prompt}"
            }]
        }]
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        # 万が一のフォールバック (gemini-pro)
        alt_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={api_key}"
        res_alt = requests.post(alt_url, headers=headers, json=payload)
        if res_alt.status_code == 200:
            return res_alt.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            raise Exception(f"AI通信エラー: {res_alt.status_code} - {res_alt.text}")

def parse_menu(text):
    items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)?', text)
    return [{"name": n, "w_def": float(re.search(r'\d+\.?\d*', w).group()) if re.search(r'\d+', w) else 0.0, 
             "sets": int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 3, 
             "r_def": int(re.search(r'\d+', r).group()) if r and re.search(r'\d+', r) else 10} for n, w, s, r in items]

# --- 5. メインUI ---
st.title("🔱 GOD-MODE AI ANALYST")
st.markdown("### 「全知全能のトレーニングログを、今ここに。」")

mode = st.selectbox("ターゲット種目", ["ベンチプレス", "スクワット", "デッドリフト"])

if st.button("文献・履歴を完全同期して生成 (FORCE CONNECT)"):
    step = (st.session_state.routine_count % 6) + 1
    target_max = st.session_state.bp_max if mode=="ベンチプレス" else st.session_state.sq_max
    target_w = round(target_max * [0.6, 0.7, 0.7, 0.75, 0.8, 0.85][step-1], 1)

    prompt = f"""
    指令：現在のサイクル Step {step}/6 に基づき、Drive文献と過去の全指示を統合してメニューを作成せよ。
    
    参照知識: {st.session_state.knowledge_base}
    過去の制約: {st.session_state.custom_constraints}
    
    メイン：『{mode}』【{target_w}kg】({step + 2}セット) 5回
    
    上記に基づき、補助種目を構成せよ。形式厳守：
    『種目名』 【重量kg】 (セット数) 回数
    """
    
    with st.spinner("🔱 AIが深層知識ベースをスキャン中..."):
        try:
            raw_text = call_gemini_api_direct(prompt)
            st.session_state.ai_thought = raw_text.split('『')[0]
            st.session_state.menu_data = parse_menu(raw_text)
            st.success("✅ AI知能の同期に成功しました。")
        except Exception as e:
            st.error(f"❌ 通信エラー: {e}")

if st.session_state.ai_thought:
    st.markdown("### 🔱 分析根拠（文献・過去ログ参照）")
    st.info(st.session_state.ai_thought)

# --- 6. 記録表示・同期エリア ---
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

    if st.button("記録を完了してDriveへ同期"):
        rows = [[datetime.now().strftime('%Y-%m-%d %H:%M'), l['name'], l['w'], l['r'], l['s']] for l in current_logs]
        if save_to_sheets(rows):
            st.balloons(); st.session_state.routine_count += 1; st.session_state.menu_data = []; st.rerun()
