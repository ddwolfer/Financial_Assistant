# Project: Quant-Analyst-Agent (777DDog)

## 1. 專案目標
構建一個自動化金融分析代理，能夠從全市場（2000+ 標的）中透過量化模型篩選出「被低估」或「具備潛力」的資產，並利用大語言模型進行深度的投行等級分析。

## 2. 技術棧 (Tech Stack)
- **語言**: Python 3.12+ (使用 `uv` 進行環境管理)
- **核心協議**: MCP (Model Context Protocol)
- **AI 整合**: Claude Skills (透過本地指令觸發)
- **數據源**: `yfinance`, `Polygon.io`, `Alpha Vantage`
- **前端展示**: Svelte 5 + Tailwind CSS (部署於 Vercel)
- **通知系統**: Telegram Bot API

## 3. 目錄結構
├── .claude/skills/        # Claude Skills 定義
├── mcp_servers/           # MCP Server 實作 (Python)
├── scripts/               # 核心邏輯腳本
│   ├── scanner/           # 第一層與第二層篩選器
│   ├── analyzer/          # 數據清理與分析準備
│   └── templates/         # 12 組投行分析 Prompt 範本
├── data/                  # 本地數據暫存 (SQLite/JSON)
├── web/                   # Svelte 5 Dashboard
└── .env                   # 金鑰管理