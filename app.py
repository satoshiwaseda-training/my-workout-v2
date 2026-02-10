import streamlit as st
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pandas as pd
import re

# --- 1. 聖域（Google Drive / Sheets）への深層接続 ---
def connect_to_sheet():
    try:
        s_acc = st.secrets["gcp_service_account"]
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive" # Driveアクセス権限を明示
        ]
        creds = Credentials.from_service_account_info(s_acc, scopes=scopes)
        client = gspread.authorize(creds)
        # 指定のスプレッドシートを開く
        sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
        return sheet
    except Exception as e:
        st.sidebar.error(f"🔱 聖域接続エラー：{e}")
        return None

# --- 2. 過去履歴の自動スキャン機能 ---
def fetch_past_logs(sheet):
    try:
        data = sheet.get_all_values()
        if len(data) > 1:
            # 最新の10件をAIに参照させるためのコンテキストとして抽出
            df = pd.DataFrame(data[1:], columns=data[0])
            return df.tail(10).to_string()
        return "過去の記録はまだありません。"
    except:
        return "データ取得失敗。"

# --- 3. 有料枠・文脈理解型 AIエンジン ---
def call_god_mode_ai(prompt, past_context):
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '')
    # 有料プラン専用 v1 エンドポイント
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    system_instruction = (
        "あなたは最強のコーチ『GOD-MODE』だ。語尾は〜だ。貴殿と呼べ。\n"
        "【絶対ルール】\n"
        "1. ベンチプレス1RM 103.5kgを絶対基準とし、提供された【過去の履歴】を分析して、成長を促す具体的な重量・回数を出せ。\n"
        "2. 脚の日は最後に必ず腹筋（アブローラー等）を追加せよ。\n"
        "3. 🔱分析根拠を冒頭に記述し、メニューはテーブル形式で提示せよ。\n"
        f"【過去の履歴データ（Drive参照）】\n{past_context}"
    )
    
    payload = {"contents": [{"parts": [{"text": f"{system_instruction}\n\n指令：{prompt}"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=30)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "🔱接続エラー。Google Cloud側の課金ステータスを確認せよ。"

# --- 4. UI 構築（以前の最高なUIの完全復元） ---
st.set_page_config(page_title="GOD-MODE PREMIER", page_icon="🔱", layout="wide")
st.title("🔱 GOD-MODE: GOOGLE ECOSYSTEM ANALYST")

# 起動時にGoogle Drive/Sheetsから履歴を自動取得
sheet = connect_to_sheet()
past_context = fetch_past_logs(sheet) if sheet else ""

# 以前のUI構成を復元
col_a, col_b = st.columns(2)
with col_a:
    program = st.selectbox("プログラム", 
                          ["ベンチプレス強化 (胸・腕)", "スクワット強化 (脚)", "デッドリフト強化 (背中・脚)", "筋肥大", "筋力増強"])
with col_b:
    targets = st.multiselect("対象部位", ["胸", "背中", "脚", "肩", "腕", "腹筋"], 
                            default=["胸"] if "ベンチ" in program else ["脚"])

intensity = st.slider("強度設定 (%)", 50, 100, 85)
memo = st.text_area("メモ・特記事項", "103.5kg基準を遵守せよ。過去の記録を超えたい。")

if st.button("🔱 履歴を参照し、分析を開始せよ"):
    with st.spinner("🔱 Google Drive の履歴を解析中..."):
        full_prompt = f"プログラム：{program}。部位：{', '.join(targets)}。強度：{intensity}%。要望：{memo}"
        response = call_god_mode_ai(full_prompt, past_context)
        st.session_state['last_response'] = response
        
        # 種目名を自動抽出して記録用プルダウンにセット
        extracted = re.findall(r"[*・]\s*([^\s(（]+)", response)
        st.session_state['menu_items'] = list(dict.fromkeys(extracted)) if extracted else ["ベンチプレス", "スクワット", "デッドリフト"]
        
        st.markdown("---")
        st.markdown(response)

# --- 5. 動的な実績記録フォーム（複数種目一括） ---
st.markdown("---")
st.subheader("🔱 本日の調練実績を記録（Google Sheetsへ同期）")

log_data_list = []
with st.form("multi_log_form"):
    for i in range(5):
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        with c1:
            default_items = st.session_state.get('menu_items', ["ベンチプレス", "スクワット"])
            ex_name = st.selectbox(f"種目 {i+1}", ["(未選択)"] + default_items, key=f"ex_{i}")
        with c2:
            ex_weight = st.text_input("重量(kg)", key=f"w_{i}")
        with c3:
            ex_reps = st.selectbox("回数", [str(n) for n in range(1, 31)], key=f"r_{i}")
        with c4:
            ex_sets = st.selectbox("セット", [str(n) for n in range(1, 11)], key=f"s_{i}")
        
        if ex_name != "(未選択)" and ex_weight:
            log_data_list.append(f"{ex_name}:{ex_weight}kgx{ex_reps}x{ex_sets}")

    if st.form_submit_button("🔱 聖典に一括刻印"):
        if log_data_list and sheet:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            full_log = " / ".join(log_data_list)
            sheet.append_row([now, program, ", ".join(targets), full_log])
            st.success(f"🔱 Google Sheetsへ保存完了：{full_log}")

# --- 6. 履歴カレンダー表示 & RPM ---
tab1, tab2 = st.tabs(["🔱 履歴（Drive同期）", "🔱 RPM計算機"])
with tab1:
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            st.dataframe(pd.DataFrame(data[1:], columns=data[0]).tail(15), use_container_width=True)
with tab2:
    w = st.number_input("重量", value=100.0)
    r = st.number_input("回数", value=1)
    st.metric("推定1RM", f"{(w * (1 + r/30)):.2f} kg")
