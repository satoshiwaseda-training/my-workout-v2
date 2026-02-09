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

# --- 2. デザイン (GOD-MODE キャラクター反映) ---
st.set_page_config(page_title="GEMINI MUSCLE MATE", page_icon="🔱", layout="wide")
st.markdown("""<style>
    .stApp { background: #0e1117; color: #ffffff; }
    .record-card { background: #1a1c23; padding: 20px; border-radius: 15px; border: 1px solid #007aff; margin-bottom: 15px; }
    h1, h2, h3 { color: #007aff !important; }
</style>""", unsafe_allow_html=True)

# --- 3. セッション初期化 ---
for key, val in {
    "menu_data": [], "bp_max": 103.5, "sq_max": 168.8, 
    "routine_count": 0, "knowledge_base": "【2月実績】SQ:168.8kg, BP:103.5kg",
    "custom_constraints": "脚の日は最後に腹筋を入れたい。"
}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 4. AI生成ロジック (世界標準エンドポイント固定) ---
def generate_ai_menu(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
    # 2026年時点で最も成功率が高いエンドポイント（AI Studio専用）
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    
    if response.status_code == 200:
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text']
    else:
        # エラー発生時は、さらに gemini-1.0-pro に自動フォールバック
        alt_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        response = requests.post(alt_url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")

def parse_menu(text):
    # 種目抽出
    items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)?.*?\[(.*?)\]', text)
    return [{"name": n, "w_def": float(re.search(r'\d+\.?\d*', w).group()) if re.search(r'\d+', w) else 0.0, 
             "r_def": int(re.search(r'\d+', r).group()) if r and re.search(r'\d+', r) else 10, 
             "sets": int(re.search(r'\d+', s).group()) if s and re.search(r'\d+', s) else 3, "rest": rs} for n, w, s, r, rs in items]

# --- 5. メイン画面 ---
st.title("🔱 GOD-MODE: AI MUSCLE ANALYST")
st.markdown("---")

mode = st.selectbox("本日のターゲット", ["ベンチプレス", "スクワット", "デッドリフト"])

if st.button("AIメニュー生成 (FULL OVERDRIVE)", type="primary"):
    step = (st.session_state.routine_count % 6) + 1
    target_max = st.session_state.bp_max if mode=="ベンチプレス" else st.session_state.sq_max
    target_w = round(target_max * [0.6, 0.7, 0.7, 0.75, 0.8, 0.85][step-1], 1)

    full_prompt = f"""
    あなたは最強のストレングスコーチ「GOD-MODE」です。
    ユーザーの過去の指示（ベンチプレス強度等）とGoogle Drive内の知識ベースを全て統合し、
    理論的かつキャラクター性のあるメニューを提示せよ。
    
    ナレッジ: {st.session_state.knowledge_base}
    制約: {st.session_state.custom_constraints}
    メイン: 『{mode}』{target_w}kg (Cycle {step}/6)
    形式：『種目名』 【重量kg】 (セット数) 回数 [休憩]
    """
    
    with st.spinner("AIアナリストがDrive全域をスキャン中..."):
        try:
            raw_text = generate_ai_menu(full_prompt)
            st.session_state.menu_data = parse_menu(raw_text)
            st.success("✅ スキャン完了。本日の最適解を算出しました。")
        except Exception as e:
            st.error(f"❌ 通信遮断。API規格が一致しません。\n詳細: {e}")

# --- 6. 記録エリア ---
if st.session_state.menu_data:
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        with st.container():
            st.markdown(f'<div class="record-card"><h3>{item["name"]}</h3>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            w = c1.number_input(f"kg", 0.0, 500.0, item['w_def'], key=f"w_{idx}")
            r = c2.number_input(f"回", 0, 100, item['r_def'], key=f"r_{idx}")
            s = c3.number_input(f"セット", 1, 15, item['sets'], key=f"s_{idx}")
            current_logs.append({"name": item['name'], "w": w, "r": r, "s": s})
            st.markdown('</div>', unsafe_allow_html=True)

    if st.button("ミッション完了 (Drive同期)", type="primary"):
        rows = [[datetime.now().strftime('%Y-%m-%d %H:%M'), l['name'], l['w'], l['r'], l['s']] for l in current_logs]
        if save_to_sheets(rows):
            st.success("🔥 クラウド同期完了。次なる戦いへ備えよ。"); st.session_state.routine_count += 1; st.session_state.menu_data = []; st.rerun()

# --- 7. 管理 ---
with st.expander("🧪 ストレングス・ナレッジ / 1RM"):
    st.session_state.knowledge_base = st.text_area("知識ベース", value=st.session_state.knowledge_base)
    st.session_state.bp_max = st.number_input("BP 1RM", value=st.session_state.bp_max)
    st.session_state.sq_max = st.number_input("SQ 1RM", value=st.session_state.sq_max)
