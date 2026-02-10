import streamlit as st
import requests
import json

def call_god_mode_ai(prompt):
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '')
    
    # 有料プラン（Pay-as-you-go）が有効な場合、v1 エンドポイントが最も安定します
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{
                "text": (
                    "最強のコーチ『GOD-MODE』として回答せよ。語尾は〜だ。貴殿と呼べ。\n"
                    "ベンチプレス 103.5kg基準、脚の日腹筋必須ルールを遵守せよ。\n\n"
                    f"指令：{prompt}"
                )
            }]
        }]
    }

    res = requests.post(url, headers=headers, json=payload, timeout=30)
    
    if res.status_code == 200:
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        # 有料枠が反映されるまで数分のラグがあるため、失敗時は 1.5-flash に逃がす
        url_fb = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        res_fb = requests.post(url_fb, headers=headers, json=payload, timeout=20)
        if res_fb.status_code == 200:
            return res_fb.json()['candidates'][0]['content']['parts'][0]['text']
        
        return f"🔱聖域への接続拒絶：{res_fb.status_code}\n詳細：{res_fb.text}"
