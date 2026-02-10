import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
import re
from datetime import datetime

# --- 1. スプレッドシート同期 ---
def save_to_sheets(rows):
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
        sheet.append_rows(rows)
        return True
    except Exception as e:
        st.error(f"Sheet Sync Error: {e}")
        return False

# --- 2. デザイン ---
st.set_page_config(page_title="GOD-MODE AI ANALYST", page_icon="🔱", layout="wide")
st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #ffffff; }
    .record-card { background: #1a1c23; padding: 25px; border-radius: 15px; border-left: 5px solid #007aff; margin-bottom: 15px; }
    .ai-thought { background: #262730; border-left: 5px solid #007aff; padding: 15px; font-style: italic; color: #d1d1d1; margin-bottom: 20px; border-radius: 0 10px 10px 0; }
    h1, h2, h3 { color: #007aff !important; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. API設定 ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 4. セッション初期化 ---
for key, val in {
    "menu_data": [], "routine_count": 0, "ai_thought": "",
    "bp_max": 103.5, "sq_max": 168.8, "dl_max": 150.0,
    "knowledge_base": "【2月実績】SQ:168.8, BP:103.5 / Drive文献：ストレングス理論、周期性トレーニング、過去のベンチプレス強度設定ログ",
    "custom_constraints": "脚の日は腹筋必須。ベンチプレスは過去の強度ルール（前回比・セット法）を完全遵守すること。"
}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 5. 文献・履歴参照 AIエンジン ---
def call_ai_analyst(prompt):
    system_instruction = """
    あなたは最強のAIストレングスアナリスト「GOD-MODE」です。
    ユーザーのGoogle Drive内の文献と、過去の全指示を完全に同期し、それに基づいた「本日の最適解」を出力してください。
    回答の冒頭には必ず「どの文献・どの履歴を根拠にしたか」を「🔱分析根拠:」として記述し、その後にメニューを記述してください。
    """
    model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
    response = model.generate_content(prompt)
    return response.text

def parse_menu(text):
    # 文献重視のAIが自由な回答をしても抽出できる堅牢な正規表現
    items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)?', text)
    menu_list = []
    for n, w, s, r in items:
        try:
            w_val = float(re.search(r'\d+\.?\d*', w).group()) if re.search(r'\d+', w) else 0.0
            s_val = int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 3
            r_val = int(re.search(r'\d+', r).group()) if r and re.search(r'\d+', r) else 10
            menu_list.append({"name": n, "w_def": w_val, "sets": s_val, "r_def": r_val})
        except:
            continue
    return menu_list

# --- 6. メインUI ---
st.title("🔱 GOD-MODE: INTELLIGENT TRAINING")

mode = st.selectbox("ターゲット種目", ["ベンチプレス", "スクワット", "デッドリフト"])

if st.button("全知識・全履歴をスキャンして生成"):
    step = (st.session_state.routine_count % 6) + 1
    target_max = st.session_state.bp_max if mode=="ベンチプレス" else st.session_state.sq_max
    target_w = round(target_max * [0.6, 0.7, 0.7, 0.75, 0.8, 0.85][step-1], 1)

    prompt = f"""
    【指令】現在のトレーニングサイクル Step {step}/6 に基づき、Drive文献と過去の全指示を統合してメニューを作成せよ。
    
    参照知識: {st.session_state.knowledge_base}
    過去の制約: {st.session_state.custom_constraints}
    
    メイン：『{mode}』【{target_w}kg】({step + 2}セット) 5回
    
    このメインを中心に、補助種目を構成せよ。形式厳守：
    『種目名』 【重量kg】 (セット数) 回数
    """
    
    with st.spinner("🔱 知識ベースを深層スキャン中..."):
        try:
            raw_text = call_ai_analyst(prompt)
            st.session_state.ai_thought = raw_text.split('『')[0]
            st.session_state.menu_data = parse_menu(raw_text)
            if not st.session_state.menu_data:
                st.warning("解析エラー。AIの出力形式を確認してください。")
        except Exception as e:
            st.error(f"AI通信エラー: {e}")

if st.session_state.ai_thought:
    st.markdown("### 🔱 AIアナリストの分析根拠")
    st.markdown(f'<div class="ai-thought">{st.session_state.ai_thought}</div>', unsafe_allow_html=True)

# --- 7. 記録・表示エリア ---
if st.session_state.menu_data:
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        st.subheader(item.get('name', '不明な種目'))
        c1, c2, c3 = st.columns(3)
        w = c1.number_input("kg", 0.0, 500.0, float(item.get('w_def', 0.0)), key=f"w_{idx}")
        r = c2.number_input("回", 0, 100, int(item.get('r_def', 10)), key=f"r_{idx}")
        s = c3.number_input("セット", 1, 15, int(item.get('sets', 3)), key=f"s_{idx}")
        current_logs.append({"name": item.get('name'), "w": w, "r": r, "s": s})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Driveへ同期してミッション完了"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        rows = [[timestamp, log['name'], log['w'], log['r'], log['s']] for log in current_logs]
        if save_to_sheets(rows):
            st.balloons()
            st.session_state.routine_count += 1
            st.session_state.menu_data = []
            st.session_state.ai_thought = ""
            st.rerun()

# --- 8. 管理パネル ---
with st.expander("🧪 AIナレッジ・ベース修正"):
    st.session_state.knowledge_base = st.text_area("参照文献・知識", value=st.session_state.knowledge_base, height=100)
    st.session_state.custom_constraints = st.text_area("過去の確定指示", value=st.session_state.custom_constraints, height=100)
    st.session_state.bp_max = st.number_input("BP 1RM", value=st.session_state.bp_max)
    st.session_state.sq_max = st.number_input("SQ 1RM", value=st.session_state.sq_max)
