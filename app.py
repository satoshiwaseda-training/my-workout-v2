import streamlit as st
import google.generativeai as genai
import re

# スマホ向け設定
st.set_page_config(page_title="AIトレ", page_icon="🏋️‍♂️")

# --- デザイン設定 ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    .proposal-box {
        background-color: #262626;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #00E5FF;
        font-size: 0.9rem;
        line-height: 1.5;
        margin-bottom: 20px;
        white-space: pre-wrap;
    }
    .record-card {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #333;
        margin-bottom: 20px;
    }
    .set-row {
        padding: 10px 0;
        border-bottom: 1px solid #333;
    }
    .set-label {
        font-size: 0.9rem;
        color: #00E5FF;
        font-weight: bold;
    }
    .stButton > button {
        width: 100%;
        height: 55px;
        border-radius: 12px;
        background-color: #00E5FF !important;
        color: #000 !important;
        font-weight: bold;
        margin-top: 20px;
    }
    .input-label {
        font-size: 0.7rem;
        color: #888;
        display: block;
        margin-bottom: 2px;
    }
    .target-hint {
        font-size: 0.85rem;
        color: #FFD700;
        font-weight: bold;
        display: block;
    }
    .rest-hint {
        font-size: 0.8rem;
        color: #00FF7F;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- APIキーの設定 ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("SecretsにGOOGLE_API_KEYが設定されていません。")

if "last_menu" not in st.session_state: st.session_state.last_menu = ""
if "menu_data" not in st.session_state: st.session_state.menu_data = []
if "feedback_history" not in st.session_state: st.session_state.feedback_history = []

st.title("🏋️‍♂️ AI TRAINER")

# --- 1. プロフィール設定 ---
with st.expander("👤 1RM設定・履歴管理"):
    c1, c2, c3 = st.columns(3)
    with c1: sq = st.number_input("SQ", 0, 500, 60)
    with c2: bp = st.number_input("BP", 0, 500, 40)
    with c3: dl = st.number_input("DL", 0, 500, 80)
    if st.button("全履歴を消去"):
        st.session_state.feedback_history = []
        st.session_state.last_menu = ""
        st.rerun()

# --- 2. プラン生成 ---
st.subheader("🔥 今日のプラン")
goal = st.selectbox("目的", ["筋肥大", "筋力向上", "維持"])
part = st.multiselect("部位", ["胸", "背中", "足", "肩", "腕", "腹筋", "全身"], default=["胸"])
equipment = st.radio("設備", ["ジム", "ダンベル", "自重"], horizontal=True)

if st.button("メニューを作成"):
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in models else models[0]
        model = genai.GenerativeModel(model_name)
        
        history = "\n".join(st.session_state.feedback_history[-3:])
        
        # 指示に「休憩時間を考慮したメニュー構成」を追加
        prompt = f"""
        あなたはプロのパーソナルトレーナーです。
        【ユーザー情報】1RM: SQ{sq}kg, BP{bp}kg, DL{dl}kg / 目的:{goal} / 部位:{part} / 設備:{equipment}
        【過去実績】:{history}

        【メニュー構成の指示】
        1. BIG3（スクワット、ベンチプレス、デッドリフト）などのコンパウンド種目は、セット間休憩を「3分」確保することを前提に、高い強度でメニューを組んでください。
        2. 全体のトレーニング時間が1時間を超えないよう、休憩時間も含めて種目数やセット数を適切に調整してください。
        3. 休憩時間は、種目の負荷（コンパウンド種目、アイソレーション種目など）に応じてAIが最適に判断してください。

        以下の形式を厳守して返してください（余計な説明不要）。
        『種目名』 【重量kg】 (セット数セット) 回数回 [休憩REST]
        """
        
        with st.spinner("AI作成中..."):
            response = model.
