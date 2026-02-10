import streamlit as st
import requests
import json

st.title("🔱 Gemini API 接続テスト (GOD-MODE)")

# Secretsからキーを取得
api_key = st.secrets["GOOGLE_API_KEY"].strip()

def run_test():
    # 接続先エンドポイント (1.5 Flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # テスト用プロンプト：あなたのデータを踏まえた質問を投げます
    test_prompt = "私の過去の記録（Muscle_LogやAmazonの購入履歴）に言及しながら、接続テストに成功したことを祝ってください。"

    payload = {
        "contents": [{"parts": [{"text": test_prompt}]}]
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            res_json = response.json()
            answer = res_json['candidates'][0]['content']['parts'][0]['text']
            st.success("✅ 接続成功！Gemini 1.5 Flash は正常に動作しています。")
            st.markdown("---")
            st.markdown(f"### AIからの返信:\n{answer}")
        else:
            st.error(f"❌ 接続失敗 (Status: {response.status_code})")
            st.code(response.text)
    except Exception as e:
        st.error(f"⚠️ エラー発生: {e}")

if st.button("接続テストを開始"):
    run_test()
