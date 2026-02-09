import streamlit as st
import google.generativeai as genai
import re
import pandas as pd
from datetime import datetime

# --- 1. 基本設定 ＆ デザイン ---
st.set_page_config(page_title="GEMINI MUSCLE MATE", page_icon="💪", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); color: #1d1d1f; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 2px solid #007aff; }
    .footer-spacer { margin-top: 150px; border-top: 1px solid #ccc; padding-top: 20px; }
    .record-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 5px solid #007aff; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 独自ルーティン設定 (Driveからの情報) ---
# 6回1サイクルのデータを定義
BENCH_ROUTINE = {
    1: {"pct": 0.60, "reps": 8, "sets": 4},
    2: {"pct": 0.70, "reps": 8, "sets": 5},
    3: {"pct": 0.70, "reps": 7, "sets": 5},
    4: {"pct": 0.70, "reps": 6, "sets": 4},
    5: {"pct": 0.80, "reps": 6, "sets": 4},
    6: {"pct": 0.85, "reps": 3, "sets": 4},
}

# --- 3. ロジック関数 ---
def calculate_1rm(w, r):
    if r <= 0: return 0
    return round(w * (1 + r / 30), 1) if r > 1 else w

def parse_menu(text):
    items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)?.*?\[(.*?)\]', text)
    menu_list = []
    for n, w, s, r, rs in items:
        w_val = float(re.search(r'\d+\.?\d*', w).group()) if re.search(r'\d+', w) else 0.0
        r_val = int(re.search(r'\d+', r).group()) if r and re.search(r'\d+', r) else 8
        s_val = int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 3
        is_c = any(x in n for x in ["ベンチプレス", "スクワット", "デッドリフト", "懸垂"])
        menu_list.append({"name": n, "w_def": w_val, "r_def": r_val, "sets": s_val, "rest": rs, "is_compound": is_c})
    return menu_list

# セッション初期化
if "GOOGLE_API_KEY" in st.secrets: genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
for key, val in {
    "total_points": 0, "history_log": {}, "calendar_events": [], 
    "menu_data": [], "last_menu_text": "", "fav_menu": "", 
    "bp_max": 115.0, "sq_max": 160.0, "dl_max": 140.0,
    "routine_count": 0  # 合計実施回数（ここから1〜6回目を算出）
}.items():
    if key not in st.session_state: st.session_state[key] = val

# 現在が何回目か算出 (1〜6)
current_cycle_step = (st.session_state.routine_count % 6) + 1

# --- 4. UI ---
with st.sidebar:
    st.markdown("## 🛠️ UNIT STATUS")
    st.write(f"現在のプログラム進行: **{current_cycle_step} / 6 回目**")
    st.progress(current_cycle_step / 6)

st.title("💪 GEMINI MUSCLE MATE")

with st.container():
    goal = st.selectbox("トレーニング目的", ["ベンチプレスを強化", "スクワットを強化", "デッドリフトを強化", "筋力向上", "筋肥大"])
    
    # 目的と部位の連動
    default_parts = ["胸"]
    if "ベンチ" in goal: default_parts = ["胸", "腕", "肩"]
    elif "スクワット" in goal: default_parts = ["足"]
    elif "デッド" in goal: default_parts = ["背中", "足"]
    
    parts = st.multiselect("対象部位", ["胸", "背中", "足", "肩", "腕", "腹筋"], default=default_parts)

    if st.button("AIメニュー生成 (INITIATE)", type="primary"):
        # ルーティンに基づくベンチプレスの設定を算出
        r_info = BENCH_ROUTINE[current_cycle_step]
        target_w = round(st.session_state.bp_max * r_info["pct"], 1)
        
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = f"""最高のコーチとして、今回の『ベンチプレス』は以下の厳格なルールでメニューに組み込んで。
            
            【今回のベンチプレス指定】
            - 重量: {target_w}kg (1RM {st.session_state.bp_max}kgの{int(r_info["pct"]*100)}%)
            - セット数: {r_info["sets"]}セット
            - レップ数: {r_info["reps"]}回
            
            【その他の優先種目】
            - 背中: 懸垂, ラットプルダウン, ベントオーバーロー
            - 胸: 上記指定のベンチを核としつつ、ナロープレス, ケーブルプレス
            - 脚: スクワット, ブルガリアンスクワット
            
            目的: {goal}, 部位: {parts}
            形式：『種目名』 【重量kg】 (セット数) 回数 [休憩]"""
            
            response = model.generate_content(prompt)
            st.session_state.last_menu_text = response.text
            st.session_state.menu_data = parse_menu(response.text)
        except:
            st.warning("⚠️ AI休憩中：バックアップを表示")

# 記録エリア (セット数増減機能付)
if st.session_state.menu_data:
    st.info(f"プログラム進行状況: 第 {current_cycle_step} ステップ（全6回中）\n{st.session_state.last_menu_text}")
    
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        col_title, col_ctrl = st.columns([3, 1])
        col_title.markdown(f"### {item['name']}")
        
        # セット数変更（AI提案値を初期値に）
        new_sets = col_ctrl.number_input("セット数", 1, 10, item['sets'], key=f"sets_num_{idx}")
        
        sets_results = []
        for s in range(new_sets):
            c1, c2, c3 = st.columns(3)
            w = c1.number_input(f"kg", 0.0, 500.0, item['w_def'], key=f"w_{idx}_{s}")
            r = c2.number_input(f"回", 0, 100, item['r_def'], key=f"r_{idx}_{s}")
            rpm = calculate_1rm(w, r)
            c3.write(f"1RM: {rpm}kg")
            sets_results.append({"w": w, "r": r, "rpm": rpm})
        
        current_logs.append({"name": item['name'], "sets": sets_results, "is_compound": item['is_compound']})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("ミッション完了！ (FINISH)", type="primary"):
        # プログラム回数をカウントアップ
        if any("ベンチプレス" in log["name"] for log in current_logs):
            st.session_state.routine_count += 1
        
        # 履歴・ポイント処理
        pts = int(sum([s['w'] * s['r'] for log in current_logs for s in log['sets']]) / 100)
        st.session_state.total_points += pts
        st.session_state.calendar_events.append(f"{datetime.now().strftime('%Y/%m/%d')} : {pts}pt (Step {current_cycle_step} 完了)")
        st.balloons()
        st.session_state.menu_data = []
        st.rerun()

# メンテナンスエリア
st.markdown('<div class="footer-spacer"></div>', unsafe_allow_html=True)
with st.expander("👤 1RM / プログラム手動調整"):
    c1, c2, c3 = st.columns(3)
    st.session_state.bp_max = c1.number_input("Bench Press 1RM", value=st.session_state.bp_max)
    st.session_state.routine_count = st.number_input("これまでの累計実施数 (0-5で現在の位置を調整)", value=st.session_state.routine_count)
