# CLAUDE.md - 專案開發規範

## 專案概述
Quant-Analyst-Agent (777DDog) — 自動化量化金融分析代理，從全市場 2000+ 標的中篩選被低估的資產，並產出投行等級的分析報告。

## 語言規範
- **程式碼註解**：使用繁體中文撰寫
- **Git commit 訊息**：使用繁體中文撰寫
- **文件**：使用繁體中文撰寫
- **變數名稱與函數名稱**：維持英文（Python 慣例）

## Git Commit 格式
```
<類型>: <繁體中文描述>

<詳細說明（繁體中文）>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

### Commit 類型
- `feat`: 新功能
- `fix`: 修復錯誤
- `chore`: 工具配置、依賴更新
- `docs`: 文件更新
- `refactor`: 重構（不改變功能）
- `test`: 測試相關

### 範例
```
feat: 新增 Layer 1 量化篩選器

- 實作 P/E、PEG、ROE、D/E 四項篩選邏輯
- 葛拉漢數計算與安全邊際百分比
- 11 個單元測試全部通過

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

## 技術棧
- **語言**: Python 3.12+（使用 `uv` 管理環境）
- **數據源**: yfinance（主要）、Polygon.io、Alpha Vantage（未來）
- **MCP**: fastmcp 框架
- **測試**: pytest
- **前端**: Svelte 5 + Tailwind CSS（未來）

## 開發指令
```bash
# 執行測試
uv run pytest tests/ -v

# === Layer 1 量化篩選 ===

# 執行 Layer 1 篩選（指定股票）
uv run python -m scripts.scanner.run_layer1 --tickers AAPL MSFT GOOGL

# 執行 Layer 1 篩選（S&P 500，絕對門檻模式）
uv run python -m scripts.scanner.run_layer1 --universe sp500 --mode absolute

# 執行 Layer 1 篩選（S&P 500，雙軌制模式 — 預設）
uv run python -m scripts.scanner.run_layer1 --universe sp500 --mode dual

# 執行 Layer 1 篩選（S&P 1500，雙軌制模式）
uv run python -m scripts.scanner.run_layer1 --universe sp1500 --mode dual

# 強制重新抓取，忽略本地快取
uv run python -m scripts.scanner.run_layer1 --universe sp500 --force-refresh

# === Layer 3 深度分析 ===

# 指定股票深度分析
uv run python -m scripts.analyzer.run_layer3 --tickers AAPL MSFT

# 從 Layer 1 結果自動載入分析
uv run python -m scripts.analyzer.run_layer3 --from-layer1

# 強制重新抓取
uv run python -m scripts.analyzer.run_layer3 --tickers AAPL --force-refresh

# 指定同業比較範圍
uv run python -m scripts.analyzer.run_layer3 --tickers AAPL --universe sp1500 --peer-count 10

# 停用 AI 白話摘要
uv run python -m scripts.analyzer.run_layer3 --tickers AAPL --no-ai-summary

# 停用價格走勢圖
uv run python -m scripts.analyzer.run_layer3 --tickers AAPL --no-chart

# === MCP 伺服器 ===

# 啟動 MCP 伺服器
uv run python mcp_servers/financial_tools.py
```

## Git 提交規範
- **定期提交**：每完成一個獨立功能或修復後，必須立即進行 git commit
- **不要累積變更**：禁止一次性提交大量不相關的變更
- **提交節奏**：每完成一個 Task 或通過一組測試後就提交
- **提交前驗證**：每次提交前必須執行 `uv run pytest tests/ -v` 確認所有測試通過

## 程式碼風格
- 函數文檔字串（docstring）使用繁體中文
- 行內註解使用繁體中文
- 遵循 PEP 8 格式規範
- 所有篩選門檻透過 `ScreeningThresholds` dataclass 設定，禁止硬編碼魔術數字
- 例外處理：所有外部 API 呼叫必須有 try/except 與重試機制

## 已知注意事項
- yfinance 的 `pegRatio` 自 2025 年 6 月起故障，需手動計算備案
- yfinance 的 `debtToEquity` 回傳百分比（如 170.5），需除以 100 轉為比率
- Yahoo Finance 有流量限制，批量抓取時需設定延遲（預設 0.1 秒）
- Layer 1 指標快取: `data/metrics_cache.json`，預設 24 小時 TTL
- Layer 3 深度分析快取: `data/deep_analysis_cache.json`，預設 24 小時 TTL
- 失敗的抓取快取 1 小時後自動重試
- 使用 `--force-refresh` 可強制重新抓取，忽略快取
- Layer 3 每支股票抓取約 4 秒（12 個 yfinance API），15 支約 60 秒
- 深度分析結果: JSON 存 `data/deep_analysis_*.json`，Markdown 存 `data/reports/*.md`
- AI 白話摘要需設定 `GEMINI_API_KEY` 環境變數，未設定時自動跳過
- AI 摘要使用 Gemini 2.0 Flash 為主，Gemini 2.5 Flash 為備援
- 價格走勢圖 PNG 存於 `data/reports/charts/`，嵌入 T1 報告
- 使用 `--no-ai-summary` 停用 AI 白話摘要，`--no-chart` 停用走勢圖

## 目錄結構
```
Financial_Assistant/
├── .claude/skills/
│   ├── scan-market/SKILL.md     # /scan-market Skill（市場篩選 SOP）
│   ├── deep-analysis/SKILL.md  # /deep-analysis Skill（深度分析 SOP）
│   └── analyze-mag7/SKILL.md   # /analyze-mag7 Skill（MAG7 科技巨頭分析）
├── mcp_servers/             # MCP 伺服器（Python）
│   └── financial_tools.py   # 六個金融工具（篩選 + 深度分析）
├── scripts/
│   ├── scanner/             # Layer 1 量化篩選器
│   │   ├── config.py        # 篩選門檻設定（含 SectorRelativeThresholds、CacheConfig）
│   │   ├── universe.py      # 股票清單載入器（S&P 500/400/600/1500）
│   │   ├── data_fetcher.py  # yfinance 數據抓取（含快取整合）
│   │   ├── metrics_cache.py # TTL 快取管理器（24h/1h）
│   │   ├── screener.py      # 絕對門檻篩選邏輯
│   │   ├── sector_screener.py # 雙軌制產業相對篩選引擎
│   │   ├── results_store.py # JSON 持久化（Layer 1 + Layer 3）
│   │   └── run_layer1.py    # Layer 1 CLI 進入點
│   └── analyzer/            # Layer 3 深度分析模組
│       ├── ai_summarizer.py      # AI 白話摘要生成器（Gemini API, Flash）
│       ├── deep_data_fetcher.py  # 深度數據抓取（6 dataclass + yfinance 12 API + 快取）
│       ├── peer_finder.py        # 同業比較器（找同業 + 批量抓取 + 排名）
│       ├── price_chart.py        # 價格走勢圖生成器（matplotlib PNG）
│       ├── report_generator.py   # Markdown 報告生成器（7 組模板 T0-T6）
│       └── run_layer3.py         # Layer 3 CLI 進入點
├── data/                    # 本地數據暫存
│   ├── metrics_cache.json          # Layer 1 指標快取
│   ├── deep_analysis_cache.json    # Layer 3 深度分析快取
│   ├── screening_*.json            # Layer 1 篩選結果
│   ├── deep_analysis_*.json        # Layer 3 分析結果
│   └── reports/                    # Layer 3 Markdown 報告
│       ├── deep_analysis_*.md
│       └── charts/                     # 價格走勢圖 PNG
├── tests/                   # 測試套件（283 個測試）
│   ├── scanner/             # Layer 1 測試（69 個）
│   ├── analyzer/            # Layer 3 測試（201 個）
│   └── test_mcp_server.py   # MCP 伺服器測試（5 個）
└── web/                     # Svelte 5 Dashboard（待開發）
```

## Layer 3 分析模板（7 組）
| # | 模板 | 分析重點 |
|---|------|---------|
| T0 | AI 白話分析摘要 | Gemini API 自動生成的白話文解讀（可停用） |
| T1 | 價值估值報告 | 價格走勢圖 + DCF 參數 + 同業倍數 + 分析師目標價 |
| T2 | 財務體質檢查 | 三表摘要 + 資產負債 + 現金流趨勢 |
| T3 | 成長動能分析 | 營收/盈餘成長 + EPS 預估 + 盈餘驚喜 |
| T4 | 風險與情境分析 | 波動性 + 放空 + 內部交易 + 機構持股 |
| T5 | 同業競爭力排名 | 5+ 同業全面對比 + 各指標排名 |
| T6 | 投資決策摘要 | 四維評估（估值/體質/成長/風險）|

## Claude Code Skills（3 個）
| Skill | 功能 |
|-------|------|
| `/scan-market` | Layer 1 市場篩選 SOP（預設 S&P 1500，雙軌制） |
| `/deep-analysis` | Layer 3 深度分析 SOP（7 組報告 + 同業比較） |
| `/analyze-mag7` | MAG7 科技巨頭分析（AAPL/MSFT/GOOGL/AMZN/NVDA/META/TSLA） |

## MCP 工具清單（6 個）
| 工具 | 功能 |
|------|------|
| `check_data_cache` | 檢查篩選快取 |
| `fetch_missing_data` | 抓取基礎指標 |
| `calculate_financial_metrics` | 計算 Graham Number + 篩選 |
| `run_sector_screening` | 雙軌制產業篩選 |
| `fetch_deep_analysis` | Layer 3 深度數據抓取 |
| `generate_analysis_report` | 生成 6 組分析報告（JSON + Markdown）|
