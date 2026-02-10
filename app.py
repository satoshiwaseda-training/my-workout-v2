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

# --- 2. デザイン (GOD-MODE キャラクター反映) ---
st.set_page_config(page_title="GOD-MODE AI ANALYST", page_icon="🔱", layout="wide")
st.markdown("""<style>
    .stApp { background: #0e1117; color: white; }
    .record-card { background: #1a1c23; padding: 25px; border-radius: 15px; border-left: 5px solid #007aff; margin-bottom: 15px; }
    .ai-badge { background: #007aff; color: white; padding: 2px 10px; border-radius: 5px; font-weight: bold; }
</style>""", unsafe_allow_html=True)

# --- 3. API初期化 (最新の公式方式) ---
# Secretsから取得し、無駄な空白を排除
API_KEY = st.secrets["GOOGLE_API_KEY"].strip()
genai.configure(api_key=API_KEY)

# --- 4. セッション初期化 (履歴・文献をここに定義) ---
for key, val in {
    "menu_data": [], "routine_count": 0, "ai_thought": "",
    "bp_max": 103.5, "sq_max": 168.8,
    "knowledge_base": "【2月実績】SQ:168.8, BP:103.5 / 文献: Google Drive内の全トレーニング学術ファイル、強度設定ログ",
    "custom_constraints": "脚の日は腹筋必須。ベンチプレスは過去の強度ルールを完全遵守。"
}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 5. 文献・履歴参照 AIエンジン ---
def call_ai_analyst(prompt):
    # 文献と履歴を重視させるシステムプロンプト
    system_instruction = """
    あなたは最強のストレングスアナリスト「GOD-MODE」です。
    ユーザーのGoogle Drive内の文献と、過去の全指示を読み込み、それに基づいた「本日の最適解」を出力してください。
    回答の冒頭には必ず「🔱分析根拠:」として、どの文献や過去のどの指示（ベンチプレスのルール等）を参考にしたか詳しく述べよ。
    """
    model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
    response = model.generate_content(prompt)
    return response.text

def parse_menu(text):
    items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)?', text)
    return [{"name": n, "w_def": float(re.search(r'\d+\.?\d*', w).group()) if re.search(r'\d+', w) else 0.0, 
             "sets": int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 3, 
             "r_def": int(re.search(r'\d+', r).group()) if r and re.search(r'\d+', r) else 10} for n, w, s, r in items]

# --- 6. メインUI ---
st.title("🔱 GOD-MODE AI ANALYST")
st.markdown("<span class='ai-badge'>GEMINI 1.5 ACTIVE</span>", unsafe_allow_html=True)

mode = st.selectbox("ターゲット", ["ベンチプレス", "スクワット", "デッドリフト"])

if st.button("全知識・全履歴を同期して生成"):
    step = (st.session_state.routine_count % 6) + 1
    target_max = st.session_state.bp_max if mode=="ベンチプレス" else st.session_state.sq_max
    target_w = round(target_max * [0.6, 0.7, 0.7, 0.75, 0.8, 0.85][step-1], 1)

    prompt = f"""
    【指令】Step {step}/6 のメニューを生成せよ。
    【ナレッジ参照】{st.session_state.knowledge_base}
    【過去履歴参照】{st.session_state.custom_constraints}
    
    メイン：『{mode}』【{target_w}kg】({step + 2}セット) 5回
    
    上記に基づき、科学的根拠のある補助種目を含めた全メニューを出力せよ。
    形式：『種目名』 【重量kg】 (セット数) 回数
    """
    
    with st.spinner("🔱 AIがクラウド知識ベースをスキャン中..."):
        try:
            raw_text = call_ai_analyst(prompt)
            st.session_state.ai_thought = raw_text.split('『')[0]
            st.session_state.menu_data = parse_menu(raw_text)
            st.success("✅ 解析完了。")
        except Exception as e:
            st.error(f"❌ 通信エラー: {e}")

if st.session_state.ai_thought:
    st.info(f"### 🔱 分析根拠\n{st.session_state.ai_thought}")

# --- 7. 記録・同期エリア ---
if st.session_state.menu_data:
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        st.subheader(item.get('name', '種目'))
        c1, c2, c3 = st.columns(3)
        w = c1.number_input("kg", 0.0, 500.0, float(item.get('w_def', 0.0)), key=f"w_{idx}")
        r = c2.number_input("回", 0, 100, int(item.get('r_def', 10)), key=f"r_{idx}")
        s = c3.number_input("セット", 1, 15, int(item.get('sets', 3)), key=f"s_{idx}")
        current_logs.append({"name": item.get('name'), "w": w, "r": r, "s": s})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("記録を完了しDriveへ同期"):
        rows = [[datetime.now().strftime('%Y-%m-%d %H:%M'), l['name'], l['w'], l['r'], l['s']] for l in current_logs]
        if save_to_sheets(rows):
            st.balloons(); st.session_state.routine_count += 1; st.session_state.menu_data = []; st.session_state.ai_thought = ""; st.rerun()

with st.expander("🧪 AIナレッジ・ベース修正"):
    st.session_state.knowledge_base = st.text_area("参照文献・知識", value=st.session_state.knowledge_base)
    st.session_state.custom_constraints = st.text_area("過去の確定指示", value=st.session_state.custom_constraints)
