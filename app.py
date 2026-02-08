import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime

# --- 1. スマホ向け基本設定 ---
st.set_page_config(page_title="AIトレPro", page_icon="💪")

# --- 2. デザイン設定 ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .proposal-box {
        background-color: #262730; padding: 15px; border-radius: 12px;
        border-left: 5px solid #FF4B4B; font-size: 0.9rem; margin-bottom: 20px;
    }
    .record-card {
        background-color: #1E1E1E; padding: 12px; border-radius: 10px;
        border: 1px solid #444; margin-bottom: 15px;
    }
    .rpm-display { color: #00E5FF; font-weight: bold; font-size: 0.8rem; margin-top: 5px; }
    .stButton > button { width: 100%; height: 50px; border-radius: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 1RM計算関数 (Epleyの式) ---
def calculate_1rm(w, r):
    if r <= 0: return 0
    if r == 1: return w
    return round(w * (1 + r / 30), 1)

# --- 4. APIキー設定 ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("SecretsにGOOGLE_API_KEYが設定されていません。")

# --- 5. セッション初期化 ---
if "last_menu" not in st.session_state: st.session_state.last_menu = ""
if "menu_data" not in st.session_state: st.session_state.menu_data = []
if "feedback_history" not in st.session_state: st.session_state.feedback_history = []
if "best_rm" not in st.session_state:
    # デフォルト値をあなたに合わせて設定
    st.session_state.best_rm = {"SQ": 160.0, "BP": 115.0, "DL": 140.0}

st.title("🏋️‍♂️ AI TRAINER Pro")

# --- 6. 1RM管理パネル ---
with st.expander("📊 自己ベスト推移・管理"):
    c1, c2, c3 = st.columns(3)
    with c1: sq = st.number_input("SQ", value=st.session_state.best_rm["SQ"])
    with c2: bp = st.number_input("BP", value=st.session_state.best_rm["BP"])
    with c3: dl = st.number_input("DL", value=st.session_state.best_rm["DL"])
    st.session_state.best_rm = {"SQ": sq, "BP": bp, "DL": dl}

# --- 7. プラン生成エリア ---
st.subheader("🔥 今日のメニュー作成")

# 目的の選択
goal = st.selectbox("目的", ["ベンチプレスを強化", "スクワットを強化", "デッドリフトを強化", "筋力向上", "筋肥大"])

# 【復活】目的に応じた部位の自動選択ロジック
default_parts = ["胸"]
if goal == "ベンチプレスを強化":
    default_parts = ["胸", "腕", "肩"]
elif goal == "スクワットを強化":
    default_parts = ["足"]
elif goal == "デッドリフトを強化":
    default_parts = ["背中", "足"]
elif goal == "筋力向上":
    default_parts = ["胸", "背中", "足"]

part = st.multiselect("対象部位", ["胸", "背中", "足", "肩", "腕", "腹筋"], default=default_parts)

if st.button("AIメニューを生成"):
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available_models else available_models[0]
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        ストレングスコーチとしてメニューを組んでください。
        【自己ベスト】SQ:{sq}kg, BP:{bp}kg, DL:{dl}kg
        【今回】目的:{goal}, 部位:{part}
        
        指示：
        1. 強化種目を最初に入れ、補助種目を3-4種目、計5種目提案。
        2. 形式厳守：『種目名』 【重量kg】 (セット数セット) 回数回 [休憩REST]
        """
        
        with st.spinner("科学的メニューを算出中..."):
            response = model.generate_content(prompt)
            st.session_state.last_menu = response.text
            items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)\s*\[(.*?)\]', response.text)
            st.session_state.menu_data = []
            for n, w, s, r, rs in items:
                # 数値を抽出してデフォルト値として使えるようにする
                weight_val = float(re.search(r'\d+\.?\d*', w).group()) if re.search(r'\d+', w) else 0.0
                reps_val = int(re.search(r'\d+', r).group()) if re.search(r'\d+', r) else 0
                sets_val = int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 3
                
                st.session_state.menu_data.append({
                    "name": n, "w_def": weight_val, "r_def": reps_val, "sets": sets_val, "rest": rs
                })
    except Exception as e:
        st.error(f"APIエラー: {e}")

# --- 8. 記録・実績入力エリア ---
if st.session_state.last_menu:
    st.markdown(f'<div class="proposal-box">{st.session_state.last_menu}</div>', unsafe_allow_html=True)
    
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        st.markdown(f"**{item['name']}** (目安: {item['rest']})")
        
        item_sets = []
        for s in range(item['sets']):
            c1, c2, c3 = st.columns([2, 2, 2])
            with c1:
                # AIが提案した重量をデフォルト値(value)として設定
                w = st.number_input("kg", 0.0, 500.0, step=2.5, key=f"w_{idx}_{s}", value=item['w_def'])
            with c2:
                # AIが提案した回数をデフォルト値(value)として設定
                r = st.number_input("回", 0, 100, step=1, key=f"r_{idx}_{s}", value=item['r_def'])
            with c3:
                rpm = calculate_1rm(w, r)
                st.markdown(f"<p class='rpm-display'>1RM: {rpm}kg</p>", unsafe_allow_html=True)
            item_sets.append(f"{w}kg×{r}回")
        
        current_logs.append(f"{item['name']}: {'/'.join(item_sets)}")
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("トレーニング完了・保存"):
        # 履歴に保存
        summary = f"{datetime.now().strftime('%Y-%m-%d')} | " + " | ".join(current_logs)
        st.session_state.feedback_history.append(summary)
        st.success("本日の記録をアプリ内に保存しました！")
