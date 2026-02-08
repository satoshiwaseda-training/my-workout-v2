import streamlit as st
import google.generativeai as genai
import re

# スマホ向け設定
st.set_page_config(page_title="AIトレ", page_icon="🏋️‍♂️")

# --- デザイン設定（スマホ特化） ---
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
        color: #00FF7F; /* 休憩時間は緑色で表示 */
        font-weight: bold;
        margin-bottom: 10px;
    }
    .stNumberInput {
        margin-bottom: 0px !important;
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
        # AIに休憩時間(REST)も計算させるよう指示を追加
        prompt = f"""
        1RM: SQ{sq}, BP{bp}, DL{dl} / 目的:{goal} / 部位:{part} / 設備:{equipment}
        過去実績:{history}

        以下の形式を厳守して日本語でメニューを返してください。
        種目の特性に合わせて最適なセット間休憩(REST)も秒または分で計算してください。
        『種目名』 【重量kg】 (セット数セット) 回数回 [休憩REST]
        """
        
        with st.spinner("AI作成中..."):
            response = model.generate_content(prompt)
            st.session_state.last_menu = response.text
            # 正規表現で休憩時間も抽出するように変更
            items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)\s*\[(.*?)\]', response.text)
            st.session_state.menu_data = [
                {"name": n, "target_w": w, "sets": int(re.search(r'\d+', s).group()), "target_r": r, "rest": rs} 
                for n, w, s, r, rs in items
            ]
    except Exception as e:
        st.error(f"エラー: {e}")

st.divider()

# --- 3. ライブ記録エリア ---
if st.session_state.last_menu:
    st.markdown("### 📋 AI提案")
    st.markdown(f'<div class="proposal-box">{st.session_state.last_menu}</div>', unsafe_allow_html=True)
    
    st.markdown("### ✍️ 実績記録")
    all_logs = []
    
    for idx, item in enumerate(st.session_state.menu_data):
        with st.container():
            st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
            st.markdown(f"**{item['name']}**", unsafe_allow_html=True)
            st.markdown(f"<span class='target-hint'>目標: {item['target_w']} × {item['target_r']}</span>", unsafe_allow_html=True)
            # 休憩時間を表示
            st.markdown(f"<span class='rest-hint'>⏱ セット間休憩: {item['rest']}</span>", unsafe_allow_html=True)
            
            item_logs = []
            for s in range(item['sets']):
                st.markdown(f'<div class="set-row">', unsafe_allow_html=True)
                c_lab, c_w, c_r = st.columns([0.8, 2.1, 2.1])
                with c_lab:
                    st.markdown(f"<p class='set-label'>S{s+1}</p>", unsafe_allow_html=True)
                with c_w:
                    st.markdown("<span class='input-label'>重量(kg)</span>", unsafe_allow_html=True)
                    w = st.number_input("kg", 0.0, 500.0, step=2.5, key=f"w_{idx}_{s}", label_visibility="collapsed")
                with c_r:
                    st.markdown("<span class='input-label'>回数</span>", unsafe_allow_html=True)
                    r = st.number_input("回", 0, 100, step=1, key=f"r_{idx}_{s}", label_visibility="collapsed")
                
                item_logs.append(f"{w}kg x {r}回")
                st.markdown('</div>', unsafe_allow_html=True)
            
            all_logs.append(f"{item['name']}: {'/'.join(item_logs)}")
            st.markdown('</div>', unsafe_allow_html=True)
    
    feeling = st.select_slider("強度感", options=["限界", "重い", "ちょうど", "軽い"])
    if st.button("トレーニング完了"):
        st.session_state.feedback_history.append(f"感想:{feeling} / 記録:" + " | ".join(all_logs))
        st.success("ナイスバルク！保存完了。")
