# Quant-Analyst-Agent (777DDog)

自動化量化金融分析代理 — 從全市場 2000+ 標的中篩選被低估的資產，並產出投行等級的分析報告。

## 功能概覽

### Layer 1: 量化篩選

從 S&P 500/400/600/1500 中，以 **雙軌制篩選** 找出被低估的標的：

- **Track 1** — 產業相對排名：P/E、PEG、ROE、D/E 在同產業的百分位排名
- **Track 2** — 安全底線過濾：排除極端值（PE > 100、D/E > 5 等）
- 輸出：Graham Number、安全邊際百分比

典型結果：S&P 500 → ~15 支（3% 通過率）

### Layer 3: 深度分析

對通過篩選的股票執行完整深度分析，產出 **6 組投行等級報告**：

| 模板 | 分析重點 |
|------|---------|
| T1 價值估值 | DCF 參數、估值倍數、分析師目標價 |
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
```

### 使用方式

```bash
# 執行 Layer 1 篩選（S&P 500，雙軌制）
uv run python -m scripts.scanner.run_layer1 --universe sp500

# 執行 Layer 3 深度分析（指定股票）
uv run python -m scripts.analyzer.run_layer3 --tickers AAPL MSFT

# 從 Layer 1 結果自動載入分析
uv run python -m scripts.analyzer.run_layer3 --from-layer1

# 執行測試
uv run pytest tests/ -v
```

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
| `generate_analysis_report` | 生成完整分析報告 |

## 技術棧

- **語言**: Python 3.12+（uv 管理）
- **數據源**: yfinance
- **MCP 框架**: fastmcp
- **測試**: pytest（247 個測試）

## 目錄結構

```
Financial_Assistant/
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
│       ├── deep_data_fetcher.py # 深度數據抓取 + 快取
│       ├── peer_finder.py       # 同業比較器
│       ├── report_generator.py  # 報告生成器（6 模板）
│       └── run_layer3.py        # CLI 進入點
├── data/                        # 數據與報告輸出
│   └── reports/                 # Markdown 報告
└── tests/                       # 測試套件（247 個）
```

## 開發狀態

- [x] Layer 1: 量化篩選（雙軌制 + 快取）
- [x] Layer 3: 深度分析（6 模板 + 同業比較）
- [x] MCP 工具整合（6 個工具）
- [ ] Claude Skill SOP
- [ ] Telegram Bot 通知
- [ ] Svelte 5 Dashboard
