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

# --- 2. 独自ルーティン設定 (BIG3共通) ---
# プログラム進行度に応じた強度設定
CYCLE_CONFIG = {
    1: {"pct": 0.60, "reps": 8, "sets": 4, "msg": "導入期。2月の実績をベースにフォームを安定させよう。"},
    2: {"pct": 0.70, "reps": 8, "sets": 5, "msg": "ボリューム期。筋持久力の限界を叩け！"},
    3: {"pct": 0.70, "reps": 7, "sets": 5, "msg": "中盤戦。集中力こそがパワーだ。"},
    4: {"pct": 0.75, "reps": 6, "sets": 4, "msg": "調整期。高重量への神経系を繋ぐよ。"},
    5: {"pct": 0.80, "reps": 5, "sets": 4, "msg": "高重量期！2月の自分を超える時が来た！"},
    6: {"pct": 0.85, "reps": 3, "sets": 4, "msg": "クライマックス。限界突破の準備はいいか？"},
}

# 2月実績データの定義
FEB_ARCHIVE = """
【2月実績ハイライト】
- ベンチプレス: 103.5kg (2/9達成)
- スクワット: 168.75kg (2/7達成)
- チンニング: 112.5kg (RM)
- ラットプルダウン: 102.5kg
"""

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
    "routine_count": 0, "file_content_cache": FEB_ARCHIVE
}.items():
    if key not in st.session_state: st.session_state[key] = val

current_cycle_step = (st.session_state.routine_count % 6) + 1
r_info = CYCLE_CONFIG[current_cycle_step]

# --- 4. UI表示 ---
with st.sidebar:
    st.markdown(f'## 🛠️ UNIT STATUS')
    st.markdown(f'''<div class="fairy-card"><span style="font-size:80px;">🔱</span><div class="system-log"><p class="log-line">> ID: GOD-MODE</p><p class="log-line">> CYCLE: {current_cycle_step}/6</p><p class="log-line">> TARGET: BIG3 READY</p></div></div>''', unsafe_allow_html=True)
    st.progress(current_cycle_step / 6)
    st.write(f"BP: {st.session_state.bp_max}kg | SQ: {st.session_state.sq_max}kg")

st.title("💪 GEMINI MUSCLE MATE")

# 1. 生成セクション (ここを拡張)
mode = st.radio("本日のフォーカス種目", ["ベンチプレス", "スクワット", "デッドリフト", "その他(筋肥大など)"], horizontal=True)
parts = st.multiselect("対象部位", ["胸", "背中", "足", "肩", "腕", "腹筋"], default=["胸"] if mode=="ベンチプレス" else ["足"] if mode=="スクワット" else ["背中"])

if st.button("AIメニュー生成 (INITIATE)", type="primary"):
    # フォーカス種目に応じた1RMと名前を選択
    if mode == "ベンチプレス":
        target_max = st.session_state.bp_max
        main_exercise = "ベンチプレス"
    elif mode == "スクワット":
        target_max = st.session_state.sq_max
        main_exercise = "スクワット"
    elif mode == "デッドリフト":
        target_max = st.session_state.dl_max
        main_exercise = "デッドリフト"
    else:
        target_max = 0
        main_exercise = ""

    target_w = round(target_max * r_info["pct"], 1) if target_max > 0 else "適正"
    
    # プロンプトの構築
    main_instr = f"【{mode}の日指定】メイン種目『{main_exercise}』を【{target_w}kg】({r_info['sets']}セット){r_info['reps']}回で必ず1種目目に設定。" if main_exercise else ""
    
    prompt = f"""
    実績データ：{st.session_state.file_content_cache}
    {main_instr}
    部位: {parts}, 目的: {mode}強化。
    筋トレMEMOの人気種目を参考に、残りのメニューを構成。
    形式：『種目名』 【重量kg】 (セット数) 回数 [休憩]
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        st.session_state.last_menu_text = response.text
    except:
        st.session_state.last_menu_text = f"『{main_exercise}』 【{target_w}kg】 ({r_info['sets']}セット) {r_info['reps']}回 [3分]"
    
    st.session_state.menu_data = parse_menu(st.session_state.last_menu_text)

# 2. 記録エリア
if st.session_state.menu_data:
    st.info(f"第 {current_cycle_step} 回ルーティン：{mode}強化モード")
    
    # 種目追加
    with st.expander("➕ 種目を手動で追加"):
        c_add1, c_add2 = st.columns([3, 1])
        new_name = c_add1.text_input("追加する種目名")
        if c_add2.button("追加"):
            if new_name:
                st.session_state.menu_data.append({"name": new_name, "w_def": 0.0, "r_def": 10, "sets": 3, "rest": "2分"})
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
        # メイン種目（BP, SQ, DL）のいずれかがあればカウントアップ
        if any(x in [log["name"] for log in current_logs] for x in ["ベンチプレス", "スクワット", "デッドリフト"]):
            st.session_state.routine_count += 1
        st.session_state.calendar_events.append(f"{datetime.now().strftime('%m/%d')} : {mode} Step{current_cycle_step}")
        st.balloons(); st.session_state.menu_data = []; st.rerun()

# 3. メンテナンスエリア
st.markdown('<div class="footer-spacer"></div>')
st.markdown("### ⚙️ SETTINGS & ARCHIVE")
with st.expander("📅 トレーニング履歴"):
    for ev in reversed(st.session_state.calendar_events): st.write(f"✅ {ev}")
with st.expander("👤 1RM / プログラム手動調整"):
    c1, c2, c3 = st.columns(3)
    st.session_state.bp_max = c1.number_input("Bench Press 1RM", value=st.session_state.bp_max)
    st.session_state.sq_max = c2.number_input("Squat 1RM", value=st.session_state.sq_max)
    st.session_state.dl_max = c3.number_input("Deadlift 1RM", value=st.session_state.dl_max)
    st.session_state.routine_count = st.number_input("現在のサイクル位置(0-5)", value=st.session_state.routine_count)
with st.expander("🧠 AI学習・こだわり設定"):
    st.write("2月学習済みデータ:")
    st.code(st.session_state.file_content_cache)
    st.session_state.fav_menu = st.text_area("こだわり", value=st.session_state.fav_menu)
