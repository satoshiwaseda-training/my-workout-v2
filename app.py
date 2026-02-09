import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
import re
from datetime import datetime

# --- 1. スプレッドシート同期関数 ---
def save_to_sheets(rows):
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
        sheet.append_rows(rows)
        return True
    except Exception as e:
        st.error(f"スプレッドシート同期エラー: {e}")
        return False

# --- 2. 基本設定 ＆ デザイン ---
st.set_page_config(page_title="GEMINI MUSCLE MATE", page_icon="💪", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); color: #1d1d1f; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 2px solid #007aff; }
    .fairy-card { background: linear-gradient(180deg, rgba(0,122,255,0.1) 0%, rgba(0,0,0,0) 100%); border-radius: 20px; padding: 25px 15px; text-align: center; border: 1px solid rgba(0,122,255,0.3); }
    .system-log { background: #111; padding: 10px; border-radius: 8px; border-left: 3px solid #00ff41; font-family: 'Consolas', monospace; text-align: left; }
    .log-line { color: #00ff41 !important; font-size: 0.8rem !important; margin: 0 !important; }
    .record-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 5px solid #007aff; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .footer-spacer { margin-top: 100px; margin-bottom: 50px; border-top: 2px solid rgba(0,0,0,0.1); }
    .ai-badge { background: #007aff; color: white; padding: 2px 10px; border-radius: 10px; font-size: 0.8rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. データ定義 ---
POPULAR_DICT = {
    "胸": ["ベンチプレス", "ダンベルフライ", "チェストプレス", "ペクトラルフライ", "インクラインDBプレス"],
    "背中": ["チンニング(懸垂)", "ラットプルダウン", "ベントオーバーロー", "シーテッドロー", "デッドリフト"],
    "足": ["スクワット", "レッグプレス", "レッグエクステンション", "ハックSQ", "V-SQ"],
    "肩": ["サイドレイズ", "ショルダープレス", "リアレイズ", "アップライトロー"],
    "腕": ["アームカール", "インクラインカール", "ナロープレス", "プレスダウン"],
    "腹筋": ["アブドミナル", "アブローラー", "レッグレイズ"]
}
CYCLE_CONFIG = {
    1: {"pct": 0.60, "reps": 8, "sets": 4, "msg": "導入期。"},
    2: {"pct": 0.70, "reps": 8, "sets": 5, "msg": "ボリューム期。"},
    3: {"pct": 0.70, "reps": 7, "sets": 5, "msg": "中盤戦。"},
    4: {"pct": 0.75, "reps": 6, "sets": 4, "msg": "調整期。"},
    5: {"pct": 0.80, "reps": 5, "sets": 4, "msg": "高重量期！"},
    6: {"pct": 0.85, "reps": 3, "sets": 4, "msg": "限界突破！"},
}

# --- 4. セッション初期化 (ここで全ての変数を準備) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

for key, val in {
    "menu_data": [], "last_menu_text": "", "ai_active": False,
    "bp_max": 103.5, "sq_max": 168.8, "dl_max": 150.0, 
    "routine_count": 0, "history_cache": [],
    "knowledge_base": "【2月実績】SQ:168.8kg, BP:103.5kg, DL:150kg",
    "custom_constraints": "脚の日は最後に腹筋を入れたい。"
}.items():
    if key not in st.session_state: st.session_state[key] = val

current_cycle_step = (st.session_state.routine_count % 6) + 1
r_info = CYCLE_CONFIG[current_cycle_step]

def parse_menu(text):
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

# --- 5. メインUI ---
with st.sidebar:
    st.markdown(f'## 🛠️ UNIT STATUS')
    engine_status = "ONLINE" if st.session_state.ai_active else "READY"
    st.markdown(f'''<div class="fairy-card"><span style="font-size:80px;">🔱</span><div class="system-log"><p class="log-line">> ID: GOD-MODE</p><p class="log-line">> SYNC: CLOUD ACTIVE</p><p class="log-line">> CORE: {engine_status}</p></div></div>''', unsafe_allow_html=True)
    st.progress(current_cycle_step / 6)

st.title("💪 GEMINI MUSCLE MATE")

mode = st.radio("フォーカス", ["ベンチプレス", "スクワット", "デッドリフト", "その他"], horizontal=True)
parts = st.multiselect("対象部位", list(POPULAR_DICT.keys()), default=["胸"] if mode=="ベンチプレス" else ["足"])

# --- AI生成ボタン (ここに全ての参照命令を統合) ---
if st.button("AIメニュー生成 (FULL SCAN MODE)", type="primary"):
    target_max = st.session_state.bp_max if mode=="ベンチプレス" else st.session_state.sq_max if mode=="スクワット" else st.session_state.dl_max
    target_w = round(target_max * r_info["pct"], 1)
    
    prompt = f"""
    あなたはユーザーの全トレーニング史とGoogle Drive内の知識ベースを統合する、専属のストレングス・アナリストです。
    
    【最優先命令】
    1. 過去の全指示（特にベンチプレス等の強度設定に関する過去のユーザーの意図）を遵守せよ。
    2. Google Drive内の「筋トレ」「ワークアウト」「論文」「実績」というキーワードを含む全ファイルの内容を参照し、理論的根拠に基づいたメニューを作成せよ。
    
    【ナレッジ/制約】
    ナレッジベース: {st.session_state.knowledge_base}
    ユーザー制約: {st.session_state.custom_constraints}
    
    【本日の設定】
    メイン:『{mode}』{target_w}kg ({r_info['sets']}set x {r_info['reps']}rep)
    部位: {parts}
    
    形式：『種目名』 【重量kg】 (セット数) 回数 [休憩]
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        st.session_state.last_menu_text = response.text
        st.session_state.ai_active = True
        st.session_state.menu_data = parse_menu(st.session_state.last_menu_text)
    except Exception as e:
        st.error(f"AI生成エラー: {e}")

# --- 記録表示エリア ---
if st.session_state.menu_data:
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        col_t, col_s, col_del = st.columns([3, 1, 0.5])
        col_t.markdown(f"### {item['name']}")
        new_sets = col_s.number_input("セット数", 1, 10, item['sets'], key=f"s_{idx}")
        if col_del.button("🗑️", key=f"del_{idx}"):
            st.session_state.menu_data.pop(idx); st.rerun()
        
        sets_data = []
        for s in range(new_sets):
            c1, c2 = st.columns(2)
            w = c1.number_input(f"kg", 0.0, 500.0, item['w_def'], key=f"w_{idx}_{s}")
            r = c2.number_input(f"回", 0, 100, item['r_def'], key=f"r_{idx}_{s}")
            sets_data.append({"w": w, "r": r})
        current_logs.append({"name": item['name'], "sets": sets_data})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("ミッション完了！ (FINISH & SYNC)", type="primary"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        rows = []
        for log in current_logs:
            for i, s in enumerate(log['sets']):
                rows.append([timestamp, log['name'], i+1, s['w'], s['r']])
        if save_to_sheets(rows):
            st.success("🔥 クラウド同期完了！")
            st.session_state.routine_count += 1
            st.session_state.history_cache.append(f"{timestamp} : {mode}完了")
            st.balloons(); st.session_state.menu_data = []; st.rerun()

# --- メンテナンスエリア ---
st.markdown('<div class="footer-spacer"></div>', unsafe_allow_html=True)
with st.expander("📅 履歴 / 👤 1RM"):
    c1, c2, c3 = st.columns(3)
    st.session_state.bp_max = c1.number_input("BP MAX", value=st.session_state.bp_max)
    st.session_state.sq_max = c2.number_input("SQ MAX", value=st.session_state.sq_max)
    st.session_state.dl_max = c3.number_input("DL MAX", value=st.session_state.dl_max)
    for ev in reversed(st.session_state.history_cache): st.write(f"✅ {ev}")

with st.expander("🧪 知識ベース（AIがDrive全域をスキャンします）"):
    st.session_state.knowledge_base = st.text_area("理論・論文・実績", value=st.session_state.knowledge_base, height=150)
    st.session_state.custom_constraints = st.text_area("こだわり・制約", value=st.session_state.custom_constraints, height=100)
