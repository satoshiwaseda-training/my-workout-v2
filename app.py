/* サイドバーを閉じる・開くボタンの視認性向上 */
    button[kind="headerNoPadding"] {
        color: #007aff !important; /* ボタン自体の色を青に */
        background-color: rgba(255, 255, 255, 0.1) !important; /* ボタンの背景を少し明るく */
        border-radius: 50% !important;
    }

    /* アイコン（<< や >>）の色を強制的に白にする */
    [data-testid="stSidebarNavSeparator"] + div button svg,
    .st-emotion-cache-6qob1r e17nll5r4 svg {
        fill: #ffffff !important;
    }

    /* サイドバー上部の閉じるボタン専用（最新のStreamlit対応） */
    [data-testid="collapsedControl"] {
        color: #ffffff !important;
        background-color: #007aff !important;
        border-radius: 0 10px 10px 0;
    }
