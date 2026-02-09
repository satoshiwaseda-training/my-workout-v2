# --- 5. AI生成ロジック（全関連ファイル・指示参照モード） ---
if st.button("AIメニュー生成 (FULL KNOWLEDGE SCAN)", type="primary"):
    target_max = st.session_state.bp_max if mode=="ベンチプレス" else st.session_state.sq_max if mode=="スクワット" else st.session_state.dl_max
    target_w = round(target_max * r_info["pct"], 1)
    
    # 修正ポイント：AIに対して「Drive内の全ファイルと過去の全指示をマインドマップせよ」と明示
    prompt = f"""
    【最優先命令】
    あなたはユーザーの全トレーニング史とGoogle Drive内の知識ベースを統合する、専属のストレングス・アナリストです。
    メニュー作成に際し、以下のリソースを「すべて」参照・統合してください：
    
    1. 過去の全指示（特にベンチプレス等の強度設定に関する過去のユーザーの意図）。
    2. Google Drive内の「筋トレ」「ワークアウト」「論文」「実績」というキーワードを含む全ファイルの内容。
    3. 以下のナレッジベースと制約。
    
    【ナレッジベース】
    {st.session_state.knowledge_base}
    
    【ユーザー制約】
    {st.session_state.custom_constraints}
    
    【本日のトレーニング構成】
    - 種目: 『{mode}』
    - 目標重量: {target_w}kg ({r_info['sets']}セット x {r_info['reps']}回)
    - サイクル進捗: Step {current_cycle_step}/6
    - フォーカス部位: {parts}
    
    出力は必ず以下の形式を守り、理論的根拠に基づいた補助種目も提案してください。
    形式：『種目名』 【重量kg】 (セット数) 回数 [休憩]
    """
    
    try:
        # 修正ポイント：より高度な推論を行うために最新のモデル設定を確認
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        st.session_state.last_menu_text = response.text
        st.session_state.ai_active = True
    except Exception as e:
        st.error(f"AIスキャンエラー: {e}")
        st.session_state.ai_active = False
