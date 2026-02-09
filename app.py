import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import random

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
st.set_page_config(page_title="GOD-MODE MUSCLE ANALYST", page_icon="🔱", layout="wide")
st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #ffffff; }
    .record-card { background: #1a1c23; padding: 20px; border-radius: 15px; border: 1px solid #007aff; margin-bottom: 15px; }
    .logic-badge { background: #007aff; color: white; padding: 2px 8px; border-radius: 5px; font-size: 0.7rem; }
    h1, h2, h3 { color: #007aff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. セッション初期化 (過去の指示・実績をここに固定) ---
if "routine_count" not in st.session_state: st.session_state.routine_count = 0
if "menu_data" not in st.session_state: st.session_state.menu_data = []

# あなたの1RM実績
BP_MAX = 103.5
SQ_MAX = 168.8
DL_MAX = 150.0

# 過去の指示・知識ベースの統合ロジック
KNOWLEDGE_LOGIC = {
    "胸": ["ベンチプレス", "インクラインDBプレス", "ダンベルフライ", "ケーブルクロスオーバー"],
    "背中": ["ラットプルダウン", "ベントオーバーローイング", "シーテッドロー", "チンニング"],
    "足": ["スクワット", "レッグプレス", "レッグエクステンション", "レッグカール"],
    "肩": ["ショルダープレス", "サイドレイズ", "リアレイズ"],
    "腹筋": ["アブドミナル", "レッグレイズ", "アブローラー"]
}

# --- 4. 究極のメニュー生成エンジン (AI通信なし) ---
def generate_perfect_menu(mode, target_max):
    step = (st.session_state.routine_count % 6) + 1
    pcts = {1:0.6, 2:0.7, 3:0.7, 4:0.75, 5:0.8, 6:0.85}
    reps = {1:8, 2:8, 3:7, 4:6, 5:5, 6:3}
    sets = {1:4, 2:5, 3:5, 4:4, 5:4, 6:4}
    
    target_w = round(target_max * pcts[step], 1)
    
    # メイン種目の構築
    menu = [{"name": mode, "w": target_w, "s": sets[step], "r": reps[step], "rest": "3-5分"}]
    
    # 補助種目の選定 (知識ベースからランダムに、かつ論理的に配置)
    parts_map = {"ベンチプレス": "胸", "スクワット": "足", "デッドリフト": "背中"}
    target_part = parts_map.get(mode, "胸")
    
    subs = random.sample(KNOWLEDGE_LOGIC[target_part], 2)
    for sub in subs:
        if sub != mode:
            menu.append({"name": sub, "w": "適正重量", "s": 3, "r": 10, "rest": "2分"})
            
    # 【過去の指示】脚の日は最後に腹筋を入れる
    if target_part == "足":
        menu.append({"name": "腹筋 (レッグレイズ)", "w": "自重", "s": 3, "r": 15, "rest": "1分"})
        
    return menu

# --- 5. メイン画面 ---
st.title("🔱 GOD-MODE: INTERNAL LOGIC ENGINE")
st.markdown(f"**STATUS: OFFLINE STABLE** <span class='logic-badge'>V2.0-CORE</span>", unsafe_allow_html=True)
st.markdown("---")

col1, col2 = st.columns(2)
mode = col1.selectbox("本日のターゲット", ["ベンチプレス", "スクワット", "デッドリフト"])
target_max = BP_MAX if mode=="ベンチプレス" else SQ_MAX if mode=="スクワット" else DL_MAX
col2.metric("現在の1RM", f"{target_max} kg")

if st.button("メニュー生成 (EXECUTE LOGIC)", type="primary"):
    st.session_state.menu_data = generate_perfect_menu(mode, target_max)
    st.success(f"✅ ロジック適用完了。Cycle Step: {(st.session_state.routine_count % 6) + 1}/6")

# --- 6. 記録エリア ---
if st.session_state.menu_data:
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        with st.container():
            st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
            st.subheader(f"{item['name']}")
            c1, c2, c3 = st.columns(3)
            # 重量が数値でない場合（"適正重量"など）の処理
            default_w = item['w'] if isinstance(item['w'], (int, float)) else 0.0
            w = c1.number_input(f"kg", 0.0, 500.0, default_w, key=f"w_{idx}")
            r = c2.number_input(f"回", 0, 100, item['r'], key=f"r_{idx}")
            s = c3.number_input(f"セット", 1, 15, item['s'], key=f"s_{idx}")
            current_logs.append({"name": item['name'], "w": w, "r": r, "s": s})
            st.markdown('</div>', unsafe_allow_html=True)

    if st.button("ミッション完了 (Drive同期)", type="primary"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        rows = [[timestamp, log['name'], log['w'], log['r'], log['s']] for log in current_logs]
        if save_to_sheets(rows):
            st.balloons()
            st.session_state.routine_count += 1
            st.session_state.menu_data = []
            st.rerun()

# --- 7. データ管理 ---
with st.expander("👤 プロフィール / 実績修正"):
    st.info("AI通信に頼らず、この設定値から直接メニューを算出します。")
    st.number_input("BP 1RM", value=BP_MAX, key="bp_val")
    st.number_input("SQ 1RM", value=SQ_MAX, key="sq_val")
