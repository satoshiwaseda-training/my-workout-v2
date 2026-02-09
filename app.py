import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime

# --- 1. 基本設定 ＆ デザイン ---
st.set_page_config(page_title="GEMINI MUSCLE MATE", page_icon="💪", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); color: #1d1d1f; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 2px solid #007aff; }
    .fairy-card { background: linear-gradient(180deg, rgba(0,122,255,0.1) 0%, rgba(0,0,0,0) 100%); border-radius: 20px; padding: 25px 15px; text-align: center; border: 1px solid rgba(0,122,255,0.3); }
    .system-log { background: #111; padding: 10px; border-radius: 8px; border-left: 3px solid #00ff41; font-family: 'Consolas', monospace; }
    .log-line { color: #00ff41 !important; font-size: 0.8rem !important; margin: 0 !important; }
    .record-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 5px solid #007aff; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .footer-spacer { margin-top: 150px; border-top: 1px solid #ccc; padding-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. データ定義 ---
POPULAR_DICT = {
    "胸": ["ベンチプレス", "ダンベルフライ", "チェストプレス", "ペクトラルフライ", "インクラインDBプレス", "ケーブルクロス"],
    "背中": ["チンニング(懸垂)", "ラットプルダウン", "ベントオーバーロー", "シーテッドロー", "ワンハンドロー", "デッドリフト"],
    "足": ["スクワット", "レッグプレス", "レッグエクステンション", "レッグカール", "ブルガリアンSQ", "ハックSQ", "V-SQ"],
    "肩": ["サイドレイズ", "ショルダープレス", "リアレイズ", "アップライトロー", "フロントレイズ"],
    "腕": ["アームカール", "インクラインカール", "ハンマーカール", "ナロープレス", "プレスダウン", "フレンチプレス"],
    "腹筋": ["アブドミナル", "アブローラー", "レッグレイズ", "クランチ"]
}

# ルーティン強度
CYCLE_CONFIG = {
    1: {"pct": 0.60, "reps": 8, "sets": 4, "msg": "導入期。2月の実績をベースに！"},
    2: {"pct": 0.70, "reps": 8, "sets": 5, "msg": "ボリューム期。筋持久力を叩け！"},
    3: {"pct": 0.70, "reps": 7, "sets": 5, "msg": "中盤戦。集中力こそがパワー。"},
    4: {"pct": 0.75, "reps": 6, "sets": 4, "msg": "調整期。高重量への神経を繋ぐ。"},
    5: {"pct": 0.80, "reps": 5, "sets": 4, "msg": "高重量期！自分を超える時！"},
    6: {"pct": 0.85, "reps": 3, "sets": 4, "msg": "限界突破の準備はいいか？"},
}

# --- 3. ロジック関数 ---
def calculate_1rm(w, r):
    if r <= 0: return 0
    return round(w * (1 + r / 30), 1) if r > 1 else w

def parse_menu(text):
    items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)?.*?\[(.*?)\]', text)
    menu_list = []
    for n, w, s, r, rs in items:
        try:
            w_match = re.search(r'\d+\.?\d*', w)
            w_val = float(w_match.group()) if w_match else 0.0
            r_match = re.search(r'\d+', r) if r else None
            r_val = int(r_match.group()) if r_match else 10
            s_match = re.search(r'\d+', s)
            s_val = int(s_match.group()) if s_match else 3
            menu_list.append({"name": n, "w_def": w_val, "r_def": r_val, "sets": s_val, "rest": rs})
        except: continue
    return menu_list

# セッション初期化
if "GOOGLE_API_KEY" in st.secrets: genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
for key, val in {
    "total_points": 2500, "calendar_events": [], "menu_data": [], 
    "last_menu_text": "", "fav_menu": "", 
    "bp_max": 103.5, "sq_max": 168.8, "dl_max": 150.0, 
    "routine_count": 0, "file_content_cache": "2月実績：BP 103.5 / SQ 168.8 / Chining 112.5"
}.items():
    if key not in st.session_state: st.session_state[key] = val

current_cycle_step = (st.session_state.routine_count % 6) + 1
r_info = CYCLE_CONFIG[current_cycle_step]

# --- 4. UI表示 ---
with st.sidebar:
    st.markdown(f'## 🛠️ UNIT STATUS')
    st.markdown(f'''<div class="fairy-card"><span style="font-size:80px;">🔱</span><div class="system-log"><p class="log-line">> ID: GOD-MODE</p><p class="log-line">> CYCLE: {current_cycle_step}/6</p></div></div>''', unsafe_allow_html=True)
    st.progress(current_cycle_step / 6)

st.title("💪 GEMINI MUSCLE MATE")

# 1. 生成セクション
mode = st.radio("フォーカス種目", ["ベンチプレス", "スクワット", "デッドリフト", "その他"], horizontal=True)
parts = st.multiselect("対象部位", list(POPULAR_DICT.keys()), default=["胸"] if mode=="ベンチプレス" else ["足"])

if st.button("AIメニュー生成 (INITIATE)", type="primary"):
    target_max = st.session_state.bp_max if mode=="ベンチプレス" else st.session_state.sq_max if mode=="スクワット" else st.session_state.dl_max
    target_w = round(target_max * r_info["pct"], 1)
    
    prompt = f"実績:{st.session_state.file_content_cache} メイン:『{mode}』{target_w}kg,{r_info['sets']}set,{r_info['reps']}rep。部位:{parts} 形式：『種目名』 【重量kg】 (セット数) 回数 [休憩]"
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        st.session_state.last_menu_text = response.text
    except:
        st.session_state.last_menu_text = f"『{mode}』 【{target_w}kg】 ({r_info['sets']}セット) {r_info['reps']}回 [3分]"
    st.session_state.menu_data = parse_menu(st.session_state.last_menu_text)

# 2. 記録 ＆ 部位別追加エリア
if st.session_state.menu_data:
    # --- 【強化】部位別スクロール（タブ）選択 ---
    with st.expander("➕ 部位から種目を選んで追加"):
        tabs = st.tabs(list(POPULAR_DICT.keys()))
        for i, (part_name, exercises) in enumerate(POPULAR_DICT.items()):
            with tabs[i]:
                selected_ex = st.selectbox(f"{part_name}の王道種目", ["-- 選択してください --"] + exercises, key=f"sel_{part_name}")
                if st.button(f"{selected_ex} を追加", key=f"btn_{part_name}"):
                    if selected_ex != "-- 選択してください --":
                        st.session_state.menu_data.append({"name": selected_ex, "w_def": 0.0, "r_def": 10, "sets": 3, "rest": "2分"})
                        st.rerun()

    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        col_t, col_s, col_del = st.columns([3, 1, 0.5])
        col_t.markdown(f"### {item['name']}")
        new_sets = col_s.number_input("セット数", 1, 10, item['sets'], key=f"s_{idx}")
        if col_del.button("🗑️", key=f"del_{idx}"):
            st.session_state.menu_data.pop(idx); st.rerun()
        
        sets_res = []
        for s in range(new_sets):
            c1, c2, c3 = st.columns(3)
            w = c1.number_input(f"kg", 0.0, 500.0, item['w_def'], key=f"w_{idx}_{s}")
            r = c2.number_input(f"回", 0, 100, item['r_def'], key=f"r_{idx}_{s}")
            sets_res.append({"w": w, "r": r, "rpm": calculate_1rm(w, r)})
        current_logs.append({"name": item['name'], "sets": sets_res})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("ミッション完了！ (FINISH)", type="primary"):
        st.session_state.routine_count += 1
        st.session_state.calendar_events.append(f"{datetime.now().strftime('%m/%d')} : {mode}完了")
        st.balloons(); st.session_state.menu_data = []; st.rerun()

# 3. メンテナンス
st.markdown('<div class="footer-spacer"></div>')
with st.expander("📅 履歴 / 👤 1RM / 🧠 学習"):
    c1, c2, c3 = st.columns(3)
    st.session_state.bp_max = c1.number_input("BP MAX", value=st.session_state.bp_max)
    st.session_state.sq_max = c2.number_input("SQ MAX", value=st.session_state.sq_max)
    st.session_state.dl_max = c3.number_input("DL MAX", value=st.session_state.dl_max)
    for ev in reversed(st.session_state.calendar_events): st.write(f"✅ {ev}")
