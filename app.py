# --- CSS部分の修正 ---
st.markdown("""
    <style>
    /* サイドバー全体の調整 */
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 2px solid #007aff;
    }

    /* キャラクターカードのデザインを刷新 */
    .fairy-card {
        background: linear-gradient(180deg, rgba(0,122,255,0.1) 0%, rgba(0,0,0,0) 100%);
        border-radius: 20px;
        padding: 25px 15px;
        text-align: center;
        border: 1px solid rgba(0,122,255,0.3);
        margin: 10px 0;
    }

    /* 卵の背後に光を当てる（後光） */
    .char-glow {
        font-size: 100px;
        filter: drop-shadow(0 0 20px rgba(255,255,255,0.4));
        margin: 20px 0;
        display: block;
    }

    /* システムテキストをより読みやすく、かつカッコよく */
    .system-log {
        background: #111;
        padding: 10px;
        border-radius: 8px;
        border-left: 3px solid #00ff41;
        font-family: 'Consolas', monospace;
        text-align: left;
        margin-top: 15px;
    }

    .log-line {
        color: #00ff41 !important;
        font-size: 0.85rem !important;
        margin: 0;
        line-height: 1.4;
    }

    /* プログレスバー（経験値）の色を青に固定 */
    .stProgress > div > div > div > div {
        background-color: #007aff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- サイドバー部分の修正 ---
with st.sidebar:
    st.markdown(f"## 🛠️ UNIT STATUS")
    
    # メインのカードエリア
    st.markdown(f'''
        <div class="fairy-card">
            <span class="char-glow">{f_emoji}</span>
            <div class="system-log">
                <p class="log-line">> ID: {f_name}</p>
                <p class="log-line">> STAT: {f_status}</p>
                <p class="log-line">> MODE: TRAINING</p>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    # 経験値エリア
    st.markdown(f"**⚡ ENERGY LEVEL**")
    st.progress(min(1.0, st.session_state.total_points / 3000))
    st.markdown(f"<p style='text-align:right; font-size:0.9rem; color:#aaa !important;'>{st.session_state.total_points} / 3000 EXP</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🏆 RECORD ARCHIVE")
    # ここも文字色を少し明るく
    st.markdown(f"""
        <p style='color:#fff !important; font-size:1rem;'>SQ: <span style='color:#00E5FF !important;'>{st.session_state.history_log.get('スクワット', 0)}kg</span></p>
        <p style='color:#fff !important; font-size:1rem;'>BP: <span style='color:#00E5FF !important;'>{st.session_state.history_log.get('ベンチプレス', 0)}kg</span></p>
        <p style='color:#fff !important; font-size:1rem;'>DL: <span style='color:#00E5FF !important;'>{st.session_state.history_log.get('デッドリフト', 0)}kg</span></p>
    """, unsafe_allow_html=True)
