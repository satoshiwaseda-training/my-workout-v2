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
    .rpm-display { color: #00E5FF; font-weight: bold; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 1RM計算関数 (Epley's formula) ---
def calculate_1rm(w, r):
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
    st.session_state.best_rm = {"SQ": 160.0, "BP": 115.0, "DL": 140.0}

st.title("🏋️‍♂️ AI TRAINER Pro")

# --- 6. 1RM管理パネル ---
with st.expander("📊 現在の自己ベスト (1RM)"):
    c1, c2, c3 = st.columns(3)
    with c1: sq = st.number_input("SQ", value=st.session_state.best_rm["SQ"])
    with c2: bp = st.number_input("BP", value=st.session_state.best_rm["BP"])
    with c3: dl = st.number_input("DL", value=st.session_state.best_rm["DL"])
    st.session_state.best_rm = {"SQ": sq, "BP": bp, "DL": dl}

# --- 7. プラン生成 ---
st.subheader("🔥 メニュー作成")
goal = st.selectbox("目的", ["筋力向上", "筋肥大", "ベンチプレス強化", "スクワット強化", "デッドリフト強化"])
part = st.multiselect("対象部位", ["胸", "背中", "足", "肩", "腕", "腹筋"], default=["胸"])

if st.button("AIプランを生成"):
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available_models else available_models[0]
        model = genai.GenerativeModel(model_name)
        
        # カレンダーからの過去データを参照するプロンプト
        prompt = f"""
        あなたはプロのストレングスコーチです。
        【自己ベスト】SQ:{sq}kg, BP:{bp}kg, DL:{dl}kg
        【今回】目的:{goal}, 部位:{part}
        過去のトレーニング履歴（{st.session_state.feedback_history[-3:]}）を考慮して、
        今日やるべき5種目程度を提案してください。
        形式：『種目名』 【重量kg】 (セット数セット) 回数回 [休憩REST]
        """
        
        with st.spinner("メニューを構成中..."):
            response = model.generate_content(prompt)
            st.session_state.last_menu = response.text
            items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)\s*\[(.*?)\]', response.text)
            st.session_state.menu_data = []
            for n, w, s, r, rs in items:
                st.session_state.menu_data.append({
                    "name": n, "target_w": w, "sets": int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 3,
                    "target_r": r, "rest": rs
                })
    except Exception as e:
        st.error(f"APIエラー: {e}")

# --- 8. 記録エリア ---
if st.session_state.last_menu:
    st.markdown(f'<div class="proposal-box">{st.session_state.last_menu}</div>', unsafe_allow_html=True)
    
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        # 現在のセットから予測されるRPMを表示
        st.markdown(f"**{item['name']}**")
        
        item_sets = []
        for s in range(item['sets']):
            c_w, c_r, c_rpm = st.columns([2, 2, 2])
            with c_w: w = st.number_input("kg", 0.0, 500.0, step=2.5, key=f"w_{idx}_{s}")
            with c_r: r = st.number_input("回", 0, 50, step=1, key=f"r_{idx}_{s}")
            with c_rpm:
                rpm = calculate_1rm(w, r)
                st.markdown(f"<p class='rpm-display'>1RM予測: {rpm}kg</p>", unsafe_allow_html=True)
            item_sets.append(f"{w}kg×{r}回")
        
        current_logs.append(f"{item['name']}({'/'.join(item_sets)})")
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("トレーニング完了・保存"):
        # 記録を履歴に保存
        summary = " | ".join(current_logs)
        st.session_state.feedback_history.append(summary)
        
        # ここでカレンダー記録や1RMの更新ロジックを走らせる
        st.success("本日のトレーニング完了！カレンダーに記録しました（想定）")
