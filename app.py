st.markdown("""
    <style>
    /* メイン背景 */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        color: #1d1d1f;
    }
    
    /* サイドバー背景 */
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 2px solid #007aff;
    }
    
    /* --- 【視認性強化】サイドバー開閉ボタンの完全な白設定 --- */
    
    /* 閉じるボタン (<<) の背景とアイコン色 */
    button[aria-label="Close sidebar"] {
        background-color: #007aff !important; /* ボタンの背景を鮮やかな青に */
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
    }
    
    button[aria-label="Close sidebar"] svg {
        fill: #ffffff !important; /* アイコンを完全な白に */
        stroke: #ffffff !important; /* 線がある場合も白に */
        filter: drop-shadow(0 0 2px rgba(255,255,255,1)); /* わずかに光らせて強調 */
    }

    /* 開くボタン (>> ※閉じている時) の背景とアイコン色 */
    button[aria-label="Open sidebar"] {
        background-color: #007aff !important;
        border-radius: 0 15px 15px 0 !important;
        padding: 10px !important;
    }
    
    button[aria-label="Open sidebar"] svg {
        fill: #ffffff !important; /* アイコンを完全な白に */
        filter: drop-shadow(0 0 2px rgba(255,255,255,1));
    }

    /* サイドバー内の文字色 */
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] .stMarkdown h1, 
    [data-testid="stSidebar"] .stMarkdown h2, 
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] label {
        color: #ffffff !important;
    }

    /* キャラクターカード・記録カード（以下、これまでのスタイルを維持） */
    .fairy-card {
        background: linear-gradient(180deg, rgba(0,122,255,0.1) 0%, rgba(0,0,0,0) 100%);
        border-radius: 20px;
        padding: 25px 15px;
        text-align: center;
        border: 1px solid rgba(0,122,255,0.3);
        margin: 10px 0;
    }
    .char-glow {
        font-size: 80px;
        filter: drop-shadow(0 0 20px rgba(255,255,255,0.4));
        display: block;
    }
    .system-log {
        background: #111;
        padding: 10px;
        border-radius: 8px;
        border-left: 3px solid #00ff41;
        font-family: 'Consolas', monospace;
    }
    .log-line {
        color: #00ff41 !important;
        font-size: 0.8rem !important;
        margin: 0 !important;
    }
    .record-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        border-left: 5px solid #007aff;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .stButton > button {
        width: 100%;
        height: 55px;
        border-radius: 12px;
        background: linear-gradient(90deg, #007aff, #00c6ff) !important;
        color: white !important;
        font-weight: bold !important;
    }
    .rpm-badge {
        background-color: #ff3b30;
        color: white !important;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)
