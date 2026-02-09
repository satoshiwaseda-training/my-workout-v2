# (前略：インポート、スプレッドシート関数、デザイン設定は維持)

# --- 4. セッション初期化（知識ベースの強化） ---
if "GOOGLE_API_KEY" in st.secrets: genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

for key, val in {
    "menu_data": [], "last_menu_text": "", "ai_active": False,
    "bp_max": 103.5, "sq_max": 168.8, "dl_max": 150.0, 
    "routine_count": 0, "history_cache": [],
    # ここに参照すべき論文の知見やメソッド、実績を格納します
    "knowledge_base": "【2月実績】SQ:168.8kg, BP:103.5kg, DL:150kg\n【参照メソッド】筋肥大にはセット間3分、1種目目はコンパウンド種目を配置。週単位のボリュームを漸進的に増やす。",
    "custom_constraints": "高重量の後は必ずアイソレーション種目でパンプさせる。腹筋は最後に追加。"
}.items():
    if key not in st.session_state: st.session_state[key] = val

# --- 5. AI生成ロジック（ここが「見に行く」核心です） ---
if st.button("AIメニュー生成 (EXECUTE WITH KNOWLEDGE)", type="primary"):
    target_max = st.session_state.bp_max if mode=="ベンチプレス" else st.session_state.sq_max if mode=="スクワット" else st.session_state.dl_max
    target_w = round(target_max * r_info["pct"], 1)
    
    # AIへの指示（知識ベースを最優先させる）
    prompt = f"""
    あなたはプロのストレングスコーチです。以下の【知識ベース】と【ユーザー制約】を厳格に守り、本日のメニューを作成してください。
    
    【知識ベース（実績・論文・メソッド）】
    {st.session_state.knowledge_base}
    
    【ユーザーの追加制約】
    {st.session_state.custom_constraints}
    
    【本日の基本設定】
    - メイン種目: 『{mode}』
    - 設定重量: {target_w}kg ({r_info['sets']}セット x {r_info['reps']}回)
    - サイクル進捗: Step {current_cycle_step}/6 ({r_info['msg']})
    - 鍛えたい部位: {parts}
    
    出力形式：『種目名』 【重量kg】 (セット数) 回数 [休憩]
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        st.session_state.last_menu_text = response.text
        st.session_state.ai_active = True
    except:
        st.session_state.last_menu_text = f"『{mode}』 【{target_w}kg】 ({r_info['sets']}セット) {r_info['reps']}回 [3分]"
        st.session_state.ai_active = False
    st.session_state.menu_data = parse_menu(st.session_state.last_menu_text)

# (中略：トレーニング記録・スプレッドシート同期エリア)

# --- 6. メンテナンスエリア（知識ベースの管理） ---
st.markdown('<div class="footer-spacer"></div>', unsafe_allow_html=True)
st.markdown("### ⚙️ SETTINGS & KNOWLEDGE BASE")

with st.expander("📅 同期履歴 / 👤 1RM調整"):
    # (既存の履歴と1RM調整コード)
    pass

with st.expander("🧪 知識ベース ＆ メソッド管理（AIが参照します）", expanded=True):
    st.write("AIがメニュー作成時に『読みに行く』ためのコア・データです。")
    st.session_state.knowledge_base = st.text_area(
        "ナレッジベース（過去実績、論文の知見、トレーニング理論など）", 
        value=st.session_state.knowledge_base, 
        height=200,
        help="ここに論文の要約や特定のメソッド（例：RPE管理、ピリオダイゼーション理論）を貼り付けてください。"
    )
    st.session_state.custom_constraints = st.text_area(
        "個人的なこだわり・制約", 
        value=st.session_state.custom_constraints, 
        height=100,
        help="怪我の有無や、特定の種目の優先順位などを入力してください。"
    )
    st.info("※ここに格納された情報を元に、AIが論理的に本日のセット数や種目構成を決定します。")
