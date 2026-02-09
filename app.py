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

# --- 2. 基本設定 & デザイン ---
st.set_page_config(page_title="GEMINI MUSCLE MATE", page_icon="💪", layout="wide")
st.markdown("""
    <style>
    .stApp { background: #f5f7fa; color: #1d1d1f; }
    .record-card { background: white; padding: 20px; border-radius: 12px; border-left: 5px solid #007aff; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .sidebar-card { background: #000; color: #fff; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. セッション初期化 ---
for key, val in {
    "menu_data": [], "bp_max": 103.5, "sq_max": 168.8, "dl_max": 150.0, 
    "routine_count": 0, "knowledge_base": "【2月実績】SQ:168.8kg, BP:103.5kg, DL:150kg",
    "custom_constraints": "脚の日は最後に腹筋を入れたい。"
}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 4. AI生成ロジック (最強の404対策版) ---
def generate_ai_menu(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"]
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    # 試行するモデルの優先順位リスト
    model_candidates = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro"
    ]
    
    last_error = ""
    for model in model_candidates:
        # v1 と v1beta の両方のエンドポイントを試行
        for version in ["v1", "v1beta"]:
            url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={api_key}"
            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
                if response.status_code == 200:
                    res_json = response.json()
                    return res_json['candidates'][0]['content']['parts'][0]['text']
                else:
                    last_error = f"{model}({version}): {response.status_code}"
                    continue
            except Exception as e:
                last_error = str(e)
                continue
    
    raise Exception(f"全モデル試行失敗。最終エラー: {last_error}")

def parse_menu(text):
    # AIの回答から『種目』【重量】(セット)などを抽出
    items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)?.*?\[(.*?)\]', text)
    menu_list = []
    for n, w, s, r, rs in items:
        try:
            w_val = float(re.search(r'\d+\.?\d*', w).group()) if re.search(r'\d+', w) else 0.0
            r_val = int(re.search(r'\d+', r).group()) if r and re.search(r'\d+', r) else 10
            s_val = int(re.search(r'\d+', s).group()) if s and re.search(r'\d+', s) else 3
            menu_list.append({"name": n, "w_def": w_val, "r_def": r_val, "sets": s_val, "rest": rs})
        except: continue
    return menu_list

# --- 5. メイン画面 ---
with st.sidebar:
    st.markdown('<div class="sidebar-card"><h1>🔱</h1><p>GOD-MODE ACTIVE</p></div>', unsafe_allow_html=True)
    st.write(f"SQ: {st.session_state.sq_max}kg / BP: {st.session_state.bp_max}kg")

st.title("💪 GEMINI MUSCLE MATE")

col_mode, col_parts = st.columns([1, 2])
mode = col_mode.radio("本日のメイン", ["ベンチプレス", "スクワット", "デッドリフト"])
parts = col_parts.multiselect("対象部位", ["胸", "背中", "足", "肩", "腕", "腹筋"], default=["胸"] if mode=="ベンチプレス" else ["足"])

if st.button("AIメニュー生成 (KNOWLEDGE SCAN)", type="primary"):
    step = (st.session_state.routine_count % 6) + 1
    pcts = {1:0.6, 2:0.7, 3:0.7, 4:0.75, 5:0.8, 6:0.85}
    target_max = st.session_state.bp_max if mode=="ベンチプレス" else st.session_state.sq_max if mode=="スクワット" else st.session_state.dl_max
    target_w = round(target_max * pcts[step], 1)

    full_prompt = f"""
    あなたはプロのストレングスコーチです。以下のリソースを全て反映させて本日のトレーニングメニューを作成してください。
    
    【最優先参照項目】
    1. Google Drive内の「筋トレ」「ワークアウト」「論文」「実績」というキーワードを含む全ファイル。
    2. 過去の全てのユーザー指示（特にベンチプレス等の強度設定）。
    
    ナレッジベース: {st.session_state.knowledge_base}
    こだわり制約: {st.session_state.custom_constraints}
    メイン: 『{mode}』 {target_w}kg ({step}/6段階目)
    対象部位: {parts}
    
    形式：『種目名』 【重量kg】 (セット数) 回数 [休憩]
    """
    with st.spinner("知識ベースをスキャン中..."):
        try:
            raw_text = generate_ai_menu(full_prompt)
            st.session_state.menu_data = parse_menu(raw_text)
            st.success("AI思考完了：知識ベースとの統合に成功しました。")
        except Exception as e:
            st.error(f"AI通信エラー: {e}")

# --- 6. トレーニング記録エリア ---
if st.session_state.menu_data:
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        st.subheader(item['name'])
        c1, c2, c3 = st.columns(3)
        w = c1.number_input(f"kg", 0.0, 500.0, item['w_def'], key=f"w_{idx}")
        r = c2.number_input(f"回", 0, 100, item['r_def'], key=f"r_{idx}")
        s = c3.number_input(f"セット", 1, 15, item['sets'], key=f"s_{idx}")
        current_logs.append({"name": item['name'], "w": w, "r": r, "s": s})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("ミッション完了 (GOOGLE DRIVE 同期)", type="primary"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        rows = [[timestamp, log['name'], log['w'], log['r'], log['s']] for log in current_logs]
        if save_to_sheets(rows):
            st.balloons()
            st.session_state.routine_count += 1
            st.session_state.menu_data = []
            st.rerun()

# --- 7. 知識ベース管理 ---
st.markdown("---")
with st.expander("🧪 知識ベース ＆ 1RM管理"):
    st.write("AIがメニュー作成時に参照する「脳」の中身です。")
    st.session_state.knowledge_base = st.text_area("理論・実績・論文要約", value=st.session_state.knowledge_base, height=150)
    st.session_state.custom_constraints = st.text_area("個人的なこだわり", value=st.session_state.custom_constraints)
    c_bp, c_sq = st.columns(2)
    st.session_state.bp_max = c_bp.number_input("BP 1RM", value=st.session_state.bp_max)
    st.session_state.sq_max = c_sq.number_input("SQ 1RM", value=st.session_state.sq_max)
