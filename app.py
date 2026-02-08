import streamlit as st
import google.generativeai as genai
import re

# --- 1. スマホ向け基本設定 ---
st.set_page_config(page_title="AIトレ", page_icon="🏋️‍♂️")

# --- 2. スマホ特化デザイン (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    .proposal-box {
        background-color: #262626; padding: 15px; border-radius: 12px;
        border-left: 5px solid #00E5FF; font-size: 0.9rem; line-height: 1.5;
        margin-bottom: 20px; white-space: pre-wrap;
    }
    .record-card {
        background-color: #1E1E1E; padding: 15px; border-radius: 12px;
        border: 1px solid #333; margin-bottom: 20px;
    }
    .set-row { padding: 10px 0; border-bottom: 1px solid #333; }
    .set-label { font-size: 0.9rem; color: #00E5FF; font-weight: bold; }
    .stButton > button {
        width: 100%; height: 50px; border-radius: 12px;
        background-color: #00E5FF !important; color: #000 !important;
        font-weight: bold; margin-top: 10px;
    }
    .input-label { font-size: 0.7rem; color: #888; display: block; margin-bottom: 2px; }
    .target-hint { font-size: 0.85rem; color: #FFD700; font-weight: bold; display: block; }
    .rest-hint { font-size: 0.8rem; color: #00FF7F; font-weight: bold; margin-bottom: 10px; }
    /* 入力欄の微調整 */
    .stNumberInput { margin-bottom: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. APIキーの設定 (Secretsから読み込み) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("SecretsにGOOGLE_API_KEYが設定されていません。")

# --- 4. セッション状態の初期化 ---
if "last_menu" not in st.session_state: st.session_state.last_menu = ""
if "menu_data" not in st.session_state: st.session_state.menu_data = []
if "feedback_history" not in st.session_state: st.session_state.feedback_history = []

st.title("🏋️‍♂️ AI TRAINER")

# --- 5. プロフィール設定 (折りたたみ) ---
with st.expander("👤 1RM設定・履歴管理"):
    c1, c2, c3 = st.columns(3)
    with c1: sq = st.number_input("SQ", 0, 500, 60)
    with c2: bp = st.number_input("BP", 0, 500, 40)
    with c3: dl = st.number_input("DL", 0, 500, 80)
    if st.button("全履歴を消去"):
        st.session_state.feedback_history = []
        st.session_state.last_menu = ""
        st.session_state.menu_data = []
        st.rerun()

# --- 6. 今日のプラン生成設定 ---
st.subheader("🔥 今日のプラン")

# 目的の選択
goal = st.selectbox("目的", ["筋肥大", "筋力向上", "ベンチプレスを強化", "スクワットを強化", "デッドリフトを強化", "維持"])

# 【部位の自動選択ロジック】
default_parts = ["胸"]
if goal == "ベンチプレスを強化":
    default_parts = ["胸", "腕", "肩"]
elif goal == "スクワットを強化":
    default_parts = ["足"]
elif goal == "デッドリフトを強化":
    default_parts = ["背中", "足"]
elif goal == "筋力向上":
    default_parts = ["胸", "背中", "足"]

part = st.multiselect("部位", ["胸", "背中", "足", "肩", "腕", "腹筋", "全身"], default=default_parts)
equipment = st.radio("設備", ["ジム", "ダンベル", "自重"], horizontal=True)

if st.button("メニューを作成"):
    try:
        # 【429エラー対策】制限の緩い 1.5-flash を優先的に探す
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available_models else available_models[0]
        model = genai.GenerativeModel(model_name)
        
        history = "\n".join(st.session_state.feedback_history[-3:])
        
        prompt = f"""
        あなたはプロのストレングスコーチです。
        【ユーザー情報】1RM: SQ{sq}kg, BP{bp}kg, DL{dl}kg / 目的:{goal} / 部位:{part} / 設備:{equipment}
        
        【指示】
        1. 目的が強化の場合、その種目を1番目に行い、その後に関連する補助種目を3-4種目、計5種目程度提案してください。
        2. BIG3などのメイン種目は休憩を3-5分、補助種目は1-2分で科学的に計算してください。
        3. 以下の形式を厳守し、余計な説明は省いてください。
        『種目名』 【重量kg】 (セット数セット) 回数回 [休憩REST]
        """
        
        with st.spinner("AIが科学的メニューを算出中..."):
            response = model.generate_content(prompt)
            st.session_state.last_menu = response.text
            
            # AIの回答からデータをパース
            items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)\s*\[(.*?)\]', response.text)
            st.session_state.menu_data = []
            for n, w, s, r, rs in items:
                set_count = int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 3
                st.session_state.menu_data.append({
                    "name": n, "target_w": w, "sets": set_count, "target_r": r, "rest": rs
                })
    except Exception as e:
        st.error(f"エラー（API制限の可能性があります）: {e}")

st.divider()

# --- 7. ライブ記録・入力エリア ---
if st.session_state.last_menu:
    st.markdown("### 📋 AI提案メニュー")
    st.markdown(f'<div class="proposal-box">{st.session_state.last_menu}</div>', unsafe_allow_html=True)
    
    st.markdown("### ✍️ 実績記録")
    
    # 予定外の種目を追加する機能
    with st.expander("➕ 予定外の種目を追加"):
        add_name = st.text_input("追加したい種目名")
        if st.button("リストに追加"):
            if add_name:
                st.session_state.menu_data.append({
                    "name": add_name, "target_w": "0kg", "sets": 3, "target_r": "10回", "rest": "2分"
                })
                st.rerun()

    all_logs = []
    
    # 各種目の入力カードを表示
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        st.markdown(f"**{item['name']}**", unsafe_allow_html=True)
        st.markdown(f"<span class='target-hint'>目標: {item['target_w']} × {item['target_r']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='rest-hint'>⏱ 休憩目安: {item['rest']}</span>", unsafe_allow_html=True)
        
        item_logs = []
        for s in range(item['sets']):
            st.markdown(f'<div class="set-row">', unsafe_allow_html=True)
            c_lab, c_w, c_r = st.columns([0.8, 2.1, 2.1])
            
            # 初期値をパースして入力欄にセット
            init_w = float(re.search(r'\d+\.?\d*', item['target_w']).group()) if re.search(r'\d+', item['target_w']) else 0.0
            init_r = int(re.search(r'\d+', item['target_r']).group()) if re.search(r'\d+', item['target_r']) else 0
            
            with c_lab:
                st.markdown(f"<p class='set-label'>S{s+1}</p>", unsafe_allow_html=True)
            with c_w:
                st.markdown("<span class='input-label'>重量(kg)</span>", unsafe_allow_html=True)
                w = st.number_input("kg", 0.0, 500.0, step=2.5, key=f"w_{idx}_{s}", value=init_w, label_visibility="collapsed")
            with c_r:
                st.markdown("<span class='input-label'>回数</span>", unsafe_allow_html=True)
                r = st.number_input("回", 0, 100, step=1, key=f"r_{idx}_{s}", value=init_r, label_visibility="collapsed")
            
            item_logs.append(f"{w}kg x {r}回")
            st.markdown('</div>', unsafe_allow_html=True)
        
        all_logs.append(f"{item['name']}: {'/'.join(item_logs)}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 全体評価と保存
    feeling = st.select_slider("今日の強度感はどうでしたか？", options=["限界", "重い", "ちょうど", "軽い"])
    
    if st.button("トレーニング完了・保存"):
        if all_logs:
            log_entry = f"記録: " + " | ".join(all_logs) + f" / 感想: {feeling}"
            st.session_state.feedback_history.append(log_entry)
            st.success("ナイスバルク！記録を保存しました。")
        else:
            st.warning("記録するデータがありません。")
