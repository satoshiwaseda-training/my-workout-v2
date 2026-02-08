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
    .set-row { padding: 10px 0; border-bottom: 1px solid #333; }
    .set-label { font-size: 0.9rem; color: #00E5FF; font-weight: bold; }
    .stButton > button {
        width: 100%; height: 50px; border-radius: 12px;
        background-color: #00E5FF !important; color: #000 !important;
        font-weight: bold; margin-top: 10px;
    }
    .add-button > div > button {
        background-color: #444 !important; color: #fff !important; height: 40px;
    }
    .input-label { font-size: 0.7rem; color: #888; display: block; margin-bottom: 2px; }
    .target-hint { font-size: 0.85rem; color: #FFD700; font-weight: bold; display: block; }
    .rest-hint { font-size: 0.8rem; color: #00FF7F; font-weight: bold; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- APIキーの設定 ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("SecretsにGOOGLE_API_KEYが設定されていません。")

# セッション状態の初期化
if "last_menu" not in st.session_state: st.session_state.last_menu = ""
if "menu_data" not in st.session_state: st.session_state.menu_data = []
if "feedback_history" not in st.session_state: st.session_state.feedback_history = []

st.title("🏋️‍♂️ AI TRAINER")

# --- 1. プロフィール設定 ---
with st.expander("👤 1RM設定・履歴管理"):
    c1, c2, c3 = st.columns(3)
    with c1: sq = st.number_input("SQ", 0, 500, 160)
    with c2: bp = st.number_input("BP", 0, 500, 115)
    with c3: dl = st.number_input("DL", 0, 500, 140)
    if st.button("全履歴を消去"):
        st.session_state.feedback_history = []
        st.session_state.last_menu = ""
        st.session_state.menu_data = []
        st.rerun()

# --- 2. プラン生成 ---
st.subheader("🔥 今日のプラン")
goal = st.selectbox("目的", ["筋肥大", "筋力向上", "ベンチプレスを強化", "スクワットを強化", "デッドリフトを強化", "維持"])
part = st.multiselect("部位", ["胸", "背中", "足", "肩", "腕", "腹筋", "全身"], default=["胸"])
equipment = st.radio("設備", ["ジム", "ダンベル", "自重"], horizontal=True)

if st.button("メニューを作成"):
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in models else models[0]
        model = genai.GenerativeModel(model_name)
        
        history = "\n".join(st.session_state.feedback_history[-3:])
        
        prompt = f"""
        あなたはプロのストレングスコーチです。
        【ユーザー情報】1RM: SQ{sq}kg, BP{bp}kg, DL{dl}kg / 目的:{goal} / 部位:{part} / 設備:{equipment}
        
        【指示】
        1. 目的が強化の場合、その種目を1番目に行い、その後に関連する補助種目（アクセサリー種目）を3〜4種目、計4〜5種目提案してください。
        2. 各種目の休憩時間を科学的根拠に基づき設定してください。
        3. 以下の形式を厳守（余計な説明不要）。
        『種目名』 【重量kg】 (セット数セット) 回数回 [休憩REST]
        """
        
        with st.spinner("メニュー算出中..."):
            response = model.generate_content(prompt)
            st.session_state.last_menu = response.text
            items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)\s*\[(.*?)\]', response.text)
            st.session_state.menu_data = [
                {"name": n, "target_w": w, "sets": int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 3, "target_r": r, "rest": rs} 
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
    
    # 手動で種目を追加する機能
    with st.expander("➕ 予定外の種目を追加"):
        add_name = st.text_input("追加する種目名")
        if st.button("リストに追加"):
            if add_name:
                st.session_state.menu_data.append({
                    "name": add_name, "target_w": "0kg", "sets": 3, "target_r": "10回", "rest": "2分"
                })
                st.rerun()

    all_logs = []
    
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        st.markdown(f"**{item['name']}**", unsafe_allow_html=True)
        st.markdown(f"<span class='target-hint'>目標: {item['target_w']} × {item['target_r']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='rest-hint'>⏱ 休憩: {item['rest']}</span>", unsafe_allow_html=True)
        
        item_logs = []
        for s in range(item['sets']):
            st.markdown(f'<div class="set-row">', unsafe_allow_html=True)
            c_lab, c_w, c_r = st.columns([0.8, 2.1, 2.1])
            with c_lab: st.markdown(f"<p class='set-label'>S{s+1}</p>", unsafe_allow_html=True)
            with c_w:
                w_val = float(re.search(r'\d+\.?\d*', item['target_w']).group()) if re.search(r'\d+', item['target_w']) else 0.0
                w = st.number_input("kg", 0.0, 500.0, step=2.5, key=f"w_{idx}_{s}", value=w_val, label_visibility="collapsed")
            with c_r:
                r_val = int(re.search(r'\d+', item['target_r']).group()) if re.search(r'\d+', item['target_r']) else 0
                r = st.number_input("回", 0, 100, step=1, key=f"r_{idx}_{s}", value=r_val, label_visibility="collapsed")
            item_logs.append(f"{w}kg x {r}回")
            st.markdown('</div>', unsafe_allow_html=True)
        
        all_logs.append(f"{item['name']}: {'/'.join(item_logs)}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    feeling = st.select_slider("強度感", options=["限界", "重い", "ちょうど", "軽い"])
    if st.button("トレーニング完了・保存"):
        st.session_state.feedback_history.append(f"記録: " + " | ".join(all_logs))
        st.success("記録完了！")

