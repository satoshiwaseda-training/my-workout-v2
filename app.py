import streamlit as st
import requests
import json

st.title("🔱 GOD-MODE: API 最終診断プロトコル")

# Secretsからキーを取得
api_key = st.secrets.get("GOOGLE_API_KEY", "").strip()

def diagnostic_test():
    if not api_key:
        st.error("APIキーがSecretsに設定されていません。")
        return

    # 2026年現在、試すべき主要モデルとバージョンの全組み合わせ
    test_configs = [
        {"model": "gemini-1.5-flash", "ver": "v1beta"},
        {"model": "gemini-1.5-pro", "ver": "v1beta"},
        {"model": "gemini-pro", "ver": "v1beta"},
        {"model": "gemini-1.5-flash", "ver": "v1"},
        {"model": "gemini-pro", "ver": "v1"}
    ]
    
    st.info("利用可能なモデルを総当たりでスキャンしています...")
    
    success_model = None
    error_logs = []

    for config in test_configs:
        model = config["model"]
        ver = config["ver"]
        url = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent?key={api_key}"
        
        payload = {"contents": [{"parts": [{"text": "接続テスト。一言で返せ。"}]}]}
        headers = {'Content-Type': 'application/json'}
        
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                success_model = f"{model} ({ver})"
                break
            else:
                error_logs.append(f"❌ {model} [{ver}]: {res.status_code} - {res.text[:100]}")
        except Exception as e:
            error_logs.append(f"⚠️ {model} [{ver}]: 通信エラー {str(e)}")

    if success_model:
        st.success(f"🎯 突破口発見！使用可能モデル: {success_model}")
        st.balloons()
        st.markdown("### AIからの応答:")
        st.write(res.json()['candidates'][0]['content']['parts'][0]['text'])
        st.info("この設定を使って本番コードを再構築します。少々お待ちください。")
    else:
        st.error("🚨 全てのモデルで疎通に失敗しました。")
        with st.expander("詳細なエラーログ（これを私に教えてください）"):
            for log in error_logs:
                st.code(log)
        
        st.warning("【考えられる原因】")
        st.write("1. **リージョン制限**: Streamlit Cloudのサーバーの場所がGemini APIの対象外である。")
        st.write("2. **キーの種類**: Google Cloud Consoleで作ったキーはURL形式が全く異なります。必ず AI Studio で作り直してください。")

if st.button("全モデル疎通テスト実行"):
    diagnostic_test()
