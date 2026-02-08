import streamlit as st
import google.generativeai as genai
import re

st.set_page_config(page_title="AIコーチ 記録Pro", page_icon="🏋️‍♂️", layout="wide")

# --- デザイン設定 ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .proposal-box { background-color: #E3F2FD; padding: 20px; border-radius: 15px; border-left: 8px solid #2196F3; }
    .record-card { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #DDD; margin-bottom: 20px; }
    .set-row { background-color: #fdfdfd; padding: 5px; border-radius: 5px; margin-bottom: 5px; border: 1px dashed #eee; }
    .target-label { color: #666; font-size: 0.85rem; font-weight: bold; }
    .stButton > button { width: 100%; border-radius: 10px; font-weight: bold; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- メモリ管理 ---
if "last_menu" not in st.session_state: st.session_state.last_menu = ""
if "menu_data" not in st.session_state: st.session_state.menu_data = []
if "feedback_history" not in st.session_state: st.session_state.feedback_history = []

st.title("🏋️‍♂️ セット別・パーソナル記録モード")

# --- 1. 設定 & BIG3 ---
with st.sidebar:
    api_key = st.text_input("Gemini API Key", type="password")
    st.divider()
    sq = st.number_input("SQUAT (kg)", 0, 500, 60)
    bp = st.number_input("BENCH (kg)", 0, 500, 40)
    dl = st.number_input("DEAD (kg)", 0, 500, 80)
    if st.button("履歴クリア"):
        st.session_state.feedback_history = []
        st.session_state.last_menu = ""
        st.rerun()

# --- 2. メニュー生成 ---
col1, col2, col3 = st.columns(3)
with col1: goal = st.selectbox("目的", ["筋肥大", "筋力向上", "健康維持"])
with col2: part = st.multiselect("部位", ["胸", "背中", "足", "肩", "腕", "腹筋", "全身"], default=["胸"])
with col3: equipment = st.radio("設備", ["ジム", "ダンベル", "自重"], horizontal=True)

if st.button("🔥 メニューを生成して記録開始！"):
    if api_key:
        try:
            genai.configure(api_key=api_key)
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model = genai.GenerativeModel(available_models[0])
            
            history = "\n".join(st.session_state.feedback_history[-3:])
            prompt = f"""
            1RM: SQ{sq}, BP{bp}, DL{dl} / 目的:{goal} / 部位:{part} / 設備:{equipment}
            【過去実績】: {history}
            
            以下の形式でメニューを作成してください。
            種目名は『』、重量は【】、セット数は（）で囲んでください。
            例：『ベンチプレス』 【50kg】 (3セット) 10回
            """
            
            with st.spinner("プランを作成中..."):
                response = model.generate_content(prompt)
                st.session_state.last_menu = response.text
                
                # AIの回答から種目名、重量、セット数を抽出
                items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)', response.text)
                st.session_state.menu_data = []
                for name, weight, set_str in items:
                    # セット数（例: "3セット"）から数字の 3 だけを取り出す
                    set_num = int(re.search(r'\d+', set_str).group()) if re.search(r'\d+', set_str) else 3
                    st.session_state.menu_data.append({"name": name, "target_w": weight, "sets": set_num})
        except Exception as e:
            st.error(f"エラー: {e}")

st.divider()

# --- 3. メインエリア ---
if st.session_state.last_menu:
    col_l, col_r = st.columns([1, 1])
    
    with col_l:
        st.markdown('### 📋 AIの提案')
        st.info(st.session_state.last_menu)
        
    with col_r:
        st.markdown('### ✍️ セット別記録')
        all_logs = []
        
        for idx, item in enumerate(st.session_state.menu_data):
            with st.container():
                st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
                st.markdown(f"**{item['name']}** (目標: {item['target_w']})")
                
                # セット数に合わせて入力欄を生成
                item_logs = []
                for s in range(item['sets']):
                    st.markdown(f'<div class="set-row">', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns([1, 2, 2])
                    with c1: st.markdown(f"<span class='target-label'>Set {s+1}</span>", unsafe_allow_html=True)
                    with c2: weight = st.number_input(f"kg", 0.0, 500.0, step=2.5, key=f"w_{idx}_{s}", label_visibility="collapsed")
                    with c3: reps = st.number_input(f"回", 0, 100, step=1, key=f"r_{idx}_{s}", label_visibility="collapsed")
                    item_logs.append(f"{weight}kg x {reps}r")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                all_logs.append(f"{item['name']}: {' / '.join(item_logs)}")
                st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("トレーニング完了・AIに送信"):
            feedback = " | ".join(all_logs)
            st.session_state.feedback_history.append(f"【実施実績】: {feedback}")
            st.success("記録完了！この内容は次回の強度調整に反映されます。")