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

# --- 2. 独自ルーティン ＆ 2月実績データのインプット ---
BENCH_ROUTINE = {
    1: {"pct": 0.60, "reps": 8, "sets": 4, "msg": "導入期。2月の粘りを思い出して！"},
    2: {"pct": 0.70, "reps": 8, "sets": 5, "msg": "ボリュームアップ。持久力勝負！"},
    3: {"pct": 0.70, "reps": 7, "sets": 5, "msg": "中盤戦。集中力を切らさないで。"},
    4: {"pct": 0.70, "reps": 6, "sets": 4, "msg": "調整局面。次から強度が上がるよ。"},
    5: {"pct": 0.80, "reps": 6, "sets": 4, "msg": "高重量域！気合入れていこう！"},
    6: {"pct": 0.85, "reps": 3, "sets": 4, "msg": "クライマックス。目標へ王手！"},
}

# 2月実績（画像から抽出した最高記録）
FEB_ARCHIVE = """
【2月実績ハイライト】
- ベンチプレス: 103.5kg (2/9達成)
- スクワット: 168.75kg (2/7達成)
- チンニング: 112.5kg (RM)
- ラットプルダウン: 102.5kg
- ナロープレス: 110.25kg
- ハックスクワット: 154.35kg
- Vスクワット: 237.5kg
- 人気種目: ベンチ、ラットプル、サイドレイズ、チンニングを多用
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

# セッション初期化（実績に基づいてBP/SQの初期値を更新）
if "GOOGLE_API_KEY" in st.secrets: genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
for key, val in {
    "total_points": 2500, "calendar_events": [], "menu_data": [], 
    "last_menu_text": "", "fav_menu": "", 
    "bp_max": 103.5, "sq_max": 168.8, "dl_max": 150.0, 
    "routine_count": 0, "file_content_cache": FEB_ARCHIVE
}.items():
    if key not in st.session_state: st.session_state[key] = val

current_cycle_step = (st.session_state.routine_count % 6) + 1
r_info = BENCH_ROUTINE[current_cycle_step]

# --- 4. UI表示 ---
with st.sidebar:
    st.markdown(f'## 🛠️ UNIT STATUS')
    st.markdown(f'''<div class="fairy-card"><span style="font-size:80px;">🔱</span><div class="system-log"><p class="log-line">> ID: GOD-MODE</p><p class="log-line">> CYCLE: {current_cycle_step}/6</p><p class="log-line">> FEB-DATA: LOADED</p></div></div>''', unsafe_allow_html=True)
    st.progress(current_cycle_step / 6)

st.title("💪 GEMINI MUSCLE MATE")

# 1. メニュー生成
goal = st.selectbox("トレーニング目的", ["ベンチプレスを強化", "筋力向上", "筋肥大"])
parts = st.multiselect("対象部位", ["胸", "背中", "足", "肩", "腕", "腹筋"], default=["胸"])

if st.button("AIメニュー生成 (INITIATE)", type="primary"):
    target_w = round(st.session_state.bp_max * r_info["pct"], 1)
    
    # 2月の実績をAIに強く意識させるプロンプト
    prompt = f"""
    あなたは超一流の筋トレコーチ。ユーザーの2月実績データを踏まえてメニューを作成せよ。
    【実績データ】: {st.session_state.file_content_cache}
    【胸の日】の場合：ベンチプレス({target_w}kg, {r_info['sets']}set, {r_info['reps']}rep)を1種目目に。
    【背中の日】の場合：実績112.5kgのチンニング、実績102.5kgのラットプルを優先。
    部位: {parts}, 目的: {goal}
    形式：『種目名』 【重量kg】 (セット数) 回数 [休憩]
    """
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        st.session_state.last_menu_text = response.text
    except:
        st.session_state.last_menu_text = f"『ベンチプレス』 【{target_w}kg】 ({r_info['sets']}セット) {r_info['reps']}回 [3分]"
    
    st.session_state.menu_data = parse_menu(st.session_state.last_menu_text)

# 2. メニュー表示・記録
if st.session_state.menu_data:
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
            w = c1.number_input("kg", 0.0, 500.0, item['w_def'], key=f"w_{idx}_{s}")
            r = c2.number_input("回", 0, 100, item['r_def'], key=f"r_{idx}_{s}")
            sets_res.append({"w": w, "r": r, "rpm": calculate_1rm(w, r)})
        current_logs.append({"name": item['name'], "sets": sets_res})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("ミッション完了！ (FINISH)", type="primary"):
        if any("ベンチプレス" in log["name"] for log in current_logs): st.session_state.routine_count += 1
        st.session_state.calendar_events.append(f"{datetime.now().strftime('%m/%d')} : 第{current_cycle_step}回完了")
        st.balloons(); st.session_state.menu_data = []; st.rerun()

# 3. メンテナンス（実績データの確認も可能に）
st.markdown('<div class="footer-spacer"></div>')
with st.expander("📅 履歴 / 👤 1RM / 🧠 学習データ"):
    st.write("**現在のAI学習ベース記録:**")
    st.code(st.session_state.file_content_cache)
    st.session_state.bp_max = st.number_input("BP 1RM(kg)", value=st.session_state.bp_max)
    st.session_state.sq_max = st.number_input("SQ 1RM(kg)", value=st.session_state.sq_max)
    for ev in reversed(st.session_state.calendar_events): st.write(f"✅ {ev}")
