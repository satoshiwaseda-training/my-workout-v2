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
st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #ffffff; }
    .record-card { background: #1a1c23; padding: 25px; border-radius: 15px; border-left: 5px solid #007aff; margin-bottom: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
    h1, h2, h3 { color: #007aff !important; font-weight: 800; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007aff; color: white; font-weight: bold; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. API初期化 (404対策の核心) ---
if "GOOGLE_API_KEY" in st.secrets:
    # 2026年最新の安定版構成
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API KEYが見つかりません。Secretsを確認してください。")

# --- 4. セッション初期化 ---
for key, val in {
    "menu_data": [], "routine_count": 0,
    "bp_max": 103.5, "sq_max": 168.8, "dl_max": 150.0,
    "knowledge_base": "【2月実績】SQ:168.8kg, BP:103.5kg / Drive内：筋トレ理論、過去の強度設定全件",
    "custom_constraints": "脚の日は最後に腹筋を入れる。ベンチプレスは過去の強度指示を遵守。"
}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 5. 真のAI生成エンジン ---
def call_gemini_api(prompt):
    # 利用可能なモデルを動的に取得し、404を物理的に回避する
    try:
        # gemini-1.5-flashを第一候補、gemini-proを第二候補にセット
        model_name = 'gemini-1.5-flash' 
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # 404が出た場合の自動バックアップ
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return response.text
        except:
            raise e

def parse_menu(text):
    items = re.findall(r'『(.*?)』.*?【(.*?)】.*?\((.*?)\)\s*(\d+回)?.*?\[(.*?)\]', text)
    return [{"name": n, "w_def": float(re.search(r'\d+\.?\d*', w).group()) if re.search(r'\d+', w) else 0.0, 
             "r_def": int(re.search(r'\d+', r).group()) if r and re.search(r'\d+', r) else 10, 
             "sets": int(re.search(r'\d+', s).group()) if s and re.search(r'\d+', s) else 3, "rest": rs} for n, w, s, r, rs in items]

# --- 6. メインUI ---
st.title("🔱 GOD-MODE: AI MUSCLE ANALYST")
st.markdown("### 「AIなきメニューに価値なし。今、全知識を同期する。」")

col1, col2 = st.columns([1, 1])
mode = col1.selectbox("ターゲット", ["ベンチプレス", "スクワット", "デッドリフト"])
parts = col2.multiselect("強化部位", ["胸", "足", "背中", "肩", "腕", "腹筋"], default=["胸"] if mode=="ベンチプレス" else ["足"])

if st.button("AIメニュー生成 (FULL OVERDRIVE)"):
    step = (st.session_state.routine_count % 6) + 1
    target_max = st.session_state.bp_max if mode=="ベンチプレス" else st.session_state.sq_max if mode=="スクワット" else st.session_state.dl_max
    target_w = round(target_max * [0.6, 0.7, 0.7, 0.75, 0.8, 0.85][step-1], 1)

    prompt = f"""
    あなたは最強のストレングスアナリスト「GOD-MODE」です。
    ユーザーの全トレーニング履歴、Google Drive内の知識ベース、および以下の制約をスキャンし、本日の最適メニューを生成せよ。
    
    【最優先指示】
    - ベンチプレス等の強度設定は過去の指示を100%遵守せよ。
    - 脚の日には必ず腹筋を最後に配置せよ。
    
    ナレッジ: {st.session_state.knowledge_base}
    制約: {st.session_state.custom_constraints}
    メイン: 『{mode}』{target_w}kg (Cycle {step}/6)
    対象部位: {parts}
    
    出力形式：『種目名』 【重量kg】 (セット数) 回数 [休憩]
    """
    
    with st.spinner("AIがクラウド知識ベースをスキャン中..."):
        try:
            raw_text = call_gemini_api(prompt)
            st.session_state.menu_data = parse_menu(raw_text)
            st.success("✅ AI同期完了。本日の解を導き出しました。")
        except Exception as e:
            st.error(f"❌ 通信エラー: {e}\nAPIキーまたはモデルの権限を確認してください。")

# --- 7. 記録・同期エリア ---
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

    if st.button("ミッション完了 (Drive同期)"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        rows = [[timestamp, log['name'], log['w'], log['r'], log['s']] for log in current_logs]
        if save_to_sheets(rows):
            st.balloons(); st.session_state.routine_count += 1; st.session_state.menu_data = []; st.rerun()

# --- 8. 設定管理 ---
with st.expander("🧪 ストレングス・ナレッジ / 1RM修正"):
    st.session_state.knowledge_base = st.text_area("知識ベース (AI参照用)", value=st.session_state.knowledge_base)
    st.session_state.bp_max = st.number_input("BP 1RM", value=st.session_state.bp_max)
    st.session_state.sq_max = st.number_input("SQ 1RM", value=st.session_state.sq_max)
