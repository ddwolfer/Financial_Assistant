# Quant-Analyst-Agent

自動化量化金融分析代理 — 從全市場 2000+ 標的中篩選被低估的資產，並產出投行等級的分析報告。

## 功能概覽

### Layer 1: 量化篩選

從 S&P 500/400/600/1500 中，以 **雙軌制篩選** 找出被低估的標的：

- **Track 1** — 產業相對排名：P/E、PEG、ROE、D/E 在同產業的百分位排名
- **Track 2** — 安全底線過濾：排除極端值（PE > 100、D/E > 5 等）
- 輸出：Graham Number、安全邊際百分比

典型結果：S&P 1500 → ~40 支（2.7% 通過率）

### Layer 3: 深度分析

對通過篩選的股票執行完整深度分析，產出 **7 組投行等級報告**：

| 模板 | 分析重點 |
|------|---------|
| T0 AI 白話摘要 | Gemini API 自動生成的白話文解讀（可停用） |
| T1 價值估值 | 價格走勢圖 + DCF 參數 + 估值倍數 + 分析師目標價 |
| T2 財務體質 | 三表摘要、資產負債表、現金流趨勢 |
| T3 成長動能 | 營收/盈餘成長、EPS 預估、盈餘驚喜 |
| T4 風險分析 | 波動性、放空比率、內部交易、機構持股 |
| T5 同業排名 | 5+ 同業全面對比、各指標排名 |
| T6 決策摘要 | 四維評估（估值/體質/成長/風險）|

輸出格式：**JSON + Markdown 雙軌輸出**

## 快速開始

### 環境需求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) 套件管理器

### 安裝

```bash
git clone https://github.com/your-repo/Financial_Assistant.git
cd Financial_Assistant
uv sync
cp .env.example .env
# 編輯 .env 填入 GEMINI_API_KEY（用於 AI 白話摘要）
```

### 使用方式

```bash
# === Layer 1 量化篩選 ===

# S&P 1500 全市場掃描（預設雙軌制）
uv run python -m scripts.scanner.run_layer1 --universe sp1500

# S&P 500 大型股篩選
uv run python -m scripts.scanner.run_layer1 --universe sp500

# 強制重新抓取，忽略快取
uv run python -m scripts.scanner.run_layer1 --universe sp500 --force-refresh

# === Layer 3 深度分析 ===

# 指定股票深度分析（含 AI 白話摘要 + 走勢圖）
uv run python -m scripts.analyzer.run_layer3 --tickers AAPL MSFT

# 從 Layer 1 結果自動載入分析
uv run python -m scripts.analyzer.run_layer3 --from-layer1

# MAG7 科技巨頭分析
uv run python -m scripts.analyzer.run_layer3 --tickers AAPL MSFT GOOGL AMZN NVDA META TSLA --universe sp500

# 停用 AI 白話摘要 / 走勢圖
uv run python -m scripts.analyzer.run_layer3 --tickers AAPL --no-ai-summary --no-chart

# === 測試 ===
uv run pytest tests/ -v
```

### 環境變數

| 變數 | 用途 | 必要性 |
|------|------|--------|
| `GEMINI_API_KEY` | AI 白話摘要（T0）| 選用，未設定時自動跳過 |
| `POLYGON_API_KEY` | 備用數據源（未來） | 選用 |
| `ALPHA_VANTAGE_API_KEY` | 備用數據源（未來） | 選用 |

### MCP 伺服器

提供 6 個工具供 Claude 使用：

```bash
uv run python mcp_servers/financial_tools.py
```

| 工具 | 功能 |
|------|------|
| `check_data_cache` | 檢查篩選快取 |
| `fetch_missing_data` | 抓取基礎指標 |
| `calculate_financial_metrics` | 計算 Graham Number + 篩選 |
| `run_sector_screening` | 雙軌制產業篩選 |
| `fetch_deep_analysis` | Layer 3 深度數據抓取 |
| `generate_analysis_report` | 生成完整分析報告（JSON + Markdown） |

### Claude Code Skills

在 Claude Code CLI 中可使用以下 Skill：

| Skill | 說明 | 觸發方式 |
|-------|------|---------|
| `/scan-market` | Layer 1 市場篩選（預設 S&P 1500） | 「掃描市場」「篩選低估股」 |
| `/deep-analysis` | Layer 3 深度分析（7 組報告） | 「分析 AAPL」「深度報告」 |
| `/analyze-mag7` | MAG7 科技巨頭分析 | 「跑 MAG7」「分析科技巨頭」 |

## 技術棧

- **語言**: Python 3.12+（uv 管理）
- **數據源**: yfinance
- **AI 摘要**: Google Gemini API（2.5 Flash）
- **MCP 框架**: fastmcp
- **測試**: pytest（283 個測試）

## 目錄結構

```
Financial_Assistant/
├── .claude/skills/
│   ├── scan-market/SKILL.md     # /scan-market Skill
│   ├── deep-analysis/SKILL.md   # /deep-analysis Skill
│   └── analyze-mag7/SKILL.md    # /analyze-mag7 Skill
├── mcp_servers/
│   └── financial_tools.py       # MCP 伺服器（6 個工具）
├── scripts/
│   ├── scanner/                 # Layer 1 量化篩選
│   │   ├── config.py            # 篩選門檻設定
│   │   ├── universe.py          # S&P 500/400/600/1500 股票清單
│   │   ├── data_fetcher.py      # yfinance 數據抓取
│   │   ├── metrics_cache.py     # TTL 快取管理
│   │   ├── screener.py          # 絕對門檻篩選
│   │   ├── sector_screener.py   # 雙軌制產業篩選
│   │   ├── results_store.py     # 結果持久化
│   │   └── run_layer1.py        # CLI 進入點
│   └── analyzer/                # Layer 3 深度分析
│       ├── ai_summarizer.py     # AI 白話摘要（Gemini API）
│       ├── deep_data_fetcher.py # 深度數據抓取 + 快取
│       ├── peer_finder.py       # 同業比較器
│       ├── price_chart.py       # 價格走勢圖（matplotlib）
│       ├── report_generator.py  # 報告生成器（7 模板 T0-T6）
│       └── run_layer3.py        # CLI 進入點
├── data/                        # 數據與報告輸出
│   └── reports/
│       ├── *.md                 # Markdown 報告
│       └── charts/              # 價格走勢圖 PNG
└── tests/                       # 測試套件（283 個）
    ├── scanner/                 # Layer 1 測試（69 個）
    ├── analyzer/                # Layer 3 測試（201 個）
    └── test_mcp_server.py       # MCP 測試（5 個）
```

## 開發狀態

- [x] Layer 1: 量化篩選（雙軌制 + 快取）
- [x] Layer 3: 深度分析（7 模板 + 同業比較）
- [x] AI 白話摘要（Gemini 2.5 Flash）
- [x] 6 個月價格走勢圖
- [x] MCP 工具整合（6 個工具）
- [x] Claude Skill SOP（`/scan-market` + `/deep-analysis` + `/analyze-mag7`）
- [ ] Telegram Bot 通知
- [ ] Svelte 5 Dashboard
