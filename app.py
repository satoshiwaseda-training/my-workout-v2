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
st.set_page_config(page_title="GEMINI MUSCLE MATE", page_icon="💪", layout="wide")
st.markdown("""<style>
    .stApp { background: #f5f7fa; color: #1d1d1f; }
    .record-card { background: white; padding: 20px; border-radius: 12px; border-left: 5px solid #007aff; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
</style>""", unsafe_allow_html=True)

# --- 3. セッション初期化 ---
for key, val in {
    "menu_data": [], "bp_max": 103.5, "sq_max": 168.8, 
    "routine_count": 0, "knowledge_base": "【2月実績】SQ:168.8kg, BP:103.5kg",
    "custom_constraints": "脚の日は最後に腹筋を入れたい。"
}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 4. AI生成ロジック (URL構成を再最適化) ---
def generate_ai_menu(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip() # 余計な空白を削除
    
    # 2026年現在、最も安定しているエンドポイント形式
    # モデル名を 'gemini-1.5-flash' に絞り、バージョンを v1beta に固定
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800,
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    
    if response.status_code == 200:
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text']
    else:
        # 詳細なエラー内容を表示して原因を特定する
        error_msg = f"Status: {response.status_code}\nResponse: {response.text}"
        raise Exception(error_msg)

def parse_menu(text):
    items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)?.*?\[(.*?)\]', text)
    return [{"name": n, "w_def": float(re.search(r'\d+\.?\d*', w).group()) if re.search(r'\d+', w) else 0.0, 
             "r_def": int(re.search(r'\d+', r).group()) if r and re.search(r'\d+', r) else 10, 
             "sets": int(re.search(r'\d+', s).group()) if s and re.search(r'\d+', s) else 3, "rest": rs} for n, w, s, r, rs in items]

# --- 5. メイン画面 ---
st.title("💪 GEMINI MUSCLE MATE")

mode = st.radio("本日のメイン", ["ベンチプレス", "スクワット", "デッドリフト"], horizontal=True)

if st.button("AIメニュー生成 (KNOWLEDGE SCAN)", type="primary"):
    step = (st.session_state.routine_count % 6) + 1
    pcts = {1:0.6, 2:0.7, 3:0.7, 4:0.75, 5:0.8, 6:0.85}
    target_max = st.session_state.bp_max if mode=="ベンチプレス" else st.session_state.sq_max
    target_w = round(target_max * pcts[step], 1)

    full_prompt = f"""
    プロのストレングスコーチとして、以下の「知識ベース」を反映しメニューを作成してください。
    【重要】Drive内の関連ファイル、過去の全指示を反映すること。
    ナレッジ: {st.session_state.knowledge_base}
    制約: {st.session_state.custom_constraints}
    メイン: 『{mode}』{target_w}kg
    形式：『種目名』 【重量kg】 (セット数) 回数 [休憩]
    """
    
    with st.spinner("AIが全知識を統合中..."):
        try:
            raw_text = generate_ai_menu(full_prompt)
            st.session_state.menu_data = parse_menu(raw_text)
            st.success("AI思考完了。")
        except Exception as e:
            # エラーの全文を表示
            st.error("AI通信エラーが発生しました。")
            st.code(str(e)) # ここに詳細が表示されます

# --- 6. 記録エリア ---
if st.session_state.menu_data:
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        with st.container():
            st.markdown(f'<div class="record-card"><h3>{item["name"]}</h3>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            w = c1.number_input(f"kg", 0.0, 500.0, item['w_def'], key=f"w_{idx}")
            r = c2.number_input(f"回", 0, 100, item['r_def'], key=f"r_{idx}")
            s = c3.number_input(f"セット", 1, 10, item['sets'], key=f"s_{idx}")
            current_logs.append({"name": item['name'], "w": w, "r": r, "s": s})
            st.markdown('</div>', unsafe_allow_html=True)

    if st.button("ミッション完了 (Drive同期)", type="primary"):
        rows = [[datetime.now().strftime('%Y-%m-%d %H:%M'), l['name'], l['w'], l['r'], l['s']] for l in current_logs]
        if save_to_sheets(rows):
            st.success("🔥 同期完了！"); st.session_state.routine_count += 1; st.session_state.menu_data = []; st.rerun()

# --- 7. 設定 ---
with st.expander("🧪 知識ベース / 1RM設定"):
    st.session_state.knowledge_base = st.text_area("理論・実績", value=st.session_state.knowledge_base)
    st.session_state.custom_constraints = st.text_area("個人的なこだわり", value=st.session_state.custom_constraints)
    st.session_state.bp_max = st.number_input("BP 1RM", value=st.session_state.bp_max)
    st.session_state.sq_max = st.number_input("SQ 1RM", value=st.session_state.sq_max)
