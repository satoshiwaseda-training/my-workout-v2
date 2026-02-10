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
    .record-card { background: #1a1c23; padding: 25px; border-radius: 15px; border: 1px solid #007aff; margin-bottom: 15px; }
    .ai-badge { background: #007aff; color: white; padding: 2px 10px; border-radius: 5px; font-weight: bold; }
    h1, h2, h3 { color: #007aff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. API設定 ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- 4. セッション初期化 (履歴と文献を重視) ---
for key, val in {
    "menu_data": [], "routine_count": 0,
    "bp_max": 103.5, "sq_max": 168.8, "dl_max": 150.0,
    "knowledge_base": "【2026年実績】SQ:168.8, BP:103.5 / 文献: Google Drive内の全トレーニング学術ファイル、過去の強度設定ログ",
    "custom_constraints": "脚の日は腹筋必須。ベンチプレスは過去の強度ルールを絶対遵守。"
}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 5. 文献・履歴参照 AIエンジン ---
def call_ai_analyst(prompt):
    # 文献と履歴を重視させるシステムプロンプト
    system_instruction = """
    あなたは最強のストレングスアナリスト「GOD-MODE」です。
    あなたの脳内には、ユーザーのGoogle Drive内の全文献と、過去の強度設定の指示がすべて記録されています。
    メニュー作成時、以下の手順を必ず踏んでください：
    1. Drive内の知識（1RM理論、セット法）を確認する。
    2. ユーザーが以前指示した「ベンチプレスのこだわり」や「強度」を優先する。
    3. それらを統合して、具体的かつ科学的なメニューを出力する。
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_instruction)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # フォールバック
        model = genai.GenerativeModel('gemini-pro', system_instruction=system_instruction)
        response = model.generate_content(prompt)
        return response.text

def parse_menu(text):
    items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)?.*?\[(.*?)\]', text)
    return [{"name": n, "w_def": float(re.search(r'\d+\.?\d*', w).group()) if re.search(r'\d+', w) else 0.0, 
             "r_def": int(re.search(r'\d+', r).group()) if r and re.search(r'\d+', r) else 10, 
             "sets": int(re.search(r'\d+', s).group()) if s and re.search(r'\d+', s) else 3, "rest": rs} for n, w, s, r, rs in items]

# --- 6. メインUI ---
st.title("🔱 GOD-MODE AI ANALYST")
st.markdown("<span class='ai-badge'>GEMINI 1.5 FLASH ACTIVE</span>", unsafe_allow_html=True)

mode = st.selectbox("ターゲット", ["ベンチプレス", "スクワット", "デッドリフト"])

if st.button("文献・履歴をスキャンしてメニュー生成"):
    step = (st.session_state.routine_count % 6) + 1
    target_max = st.session_state.bp_max if mode=="ベンチプレス" else st.session_state.sq_max
    target_w = round(target_max * [0.6, 0.7, 0.7, 0.75, 0.8, 0.85][step-1], 1)

    prompt = f"""
    【分析依頼】
    現在のサイクル: Step {step}/6
    メイン重量: {target_w}kg
    
    【参照データ】
    1. ユーザーの過去の指示: {st.session_state.custom_constraints}
    2. 参照文献・ナレッジ: {st.session_state.knowledge_base}
    
    上記を統合し、本日のメニューを以下の形式で出力せよ。
    『種目名』 【重量kg】 (セット数) 回数 [休憩]
    """
    
    with st.spinner("Drive文献と過去の指示を統合中..."):
        try:
            raw_text = call_ai_analyst(prompt)
            st.session_state.menu_data = parse_menu(raw_text)
            st.write("### AIの分析結果")
            st.info(raw_text) # AIの思考（生データ）を一度表示して確認させる
        except Exception as e:
            st.error(f"通信エラー: {e}")

# --- 7. 記録エリア ---
if st.session_state.menu_data:
    current_logs = []
    for idx, item in enumerate(st.session_state.menu_data):
        st.markdown(f'<div class="record-card">', unsafe_allow_html=True)
        st.subheader(item['name'])
        c1, c2, c3 = st.columns(3)
        w = c1.number_input("kg", 0.0, 500.0, item['w_def'], key=f"w_{idx}")
        r = c2.number_input("回", 0, 100, item['r_def'], key=f"r_{idx}")
        s = c3.number_input("セット", 1, 15, item['sets'], key=f"s_{idx}")
        current_logs.append({"name": item['name'], "w": w, "r": r, "s": s})
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("記録を完了しDriveへ同期"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        rows = [[timestamp, log['name'], log['w'], log['r'], log['s']] for log in current_logs]
        if save_to_sheets(rows):
            st.balloons(); st.session_state.routine_count += 1; st.session_state.menu_data = []; st.rerun()

# --- 8. 文献・履歴の修正 ---
with st.expander("🧪 AIへの知識提供（文献・過去の指示を編集）"):
    st.session_state.knowledge_base = st.text_area("参照文献・知識", value=st.session_state.knowledge_base, height=150)
    st.session_state.custom_constraints = st.text_area("過去の確定指示（ベンチプレスのルール等）", value=st.session_state.custom_constraints, height=100)
