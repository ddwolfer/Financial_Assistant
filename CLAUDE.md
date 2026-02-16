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

# 執行 Layer 1 篩選（指定股票）
uv run python -m scripts.scanner.run_layer1 --tickers AAPL MSFT GOOGL

# 執行 Layer 1 篩選（S&P 500，絕對門檻模式）
uv run python -m scripts.scanner.run_layer1 --universe sp500 --mode absolute

# 執行 Layer 1 篩選（S&P 500，雙軌制模式 — 預設）
uv run python -m scripts.scanner.run_layer1 --universe sp500 --mode dual

# 執行 Layer 1 篩選（S&P 1500，雙軌制模式）
uv run python -m scripts.scanner.run_layer1 --universe sp1500 --mode dual

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

## 目錄結構
```
Financial_Assistant/
├── .claude/skills/          # Claude Skills 定義
├── mcp_servers/             # MCP 伺服器（Python）
│   └── financial_tools.py   # 四個金融工具（含雙軌制篩選）
├── scripts/
│   ├── scanner/             # Layer 1 量化篩選器
│   │   ├── config.py        # 篩選門檻設定（含 SectorRelativeThresholds）
│   │   ├── universe.py      # 股票清單載入器（S&P 500/400/600/1500）
│   │   ├── data_fetcher.py  # yfinance 數據抓取
│   │   ├── screener.py      # 絕對門檻篩選邏輯
│   │   ├── sector_screener.py # 雙軌制產業相對篩選引擎
│   │   ├── results_store.py # JSON 持久化
│   │   └── run_layer1.py    # CLI 進入點（支援 --mode dual/absolute）
│   ├── analyzer/            # 數據清理（待開發）
│   └── templates/           # 12 組分析範本（待開發）
├── data/                    # 本地數據暫存
├── tests/                   # 測試套件（56 個測試）
└── web/                     # Svelte 5 Dashboard（待開發）
```
