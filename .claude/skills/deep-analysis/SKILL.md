---
name: deep-analysis
description: >
  深度分析 SOP — 對指定股票執行完整深度分析，產出投行等級報告。
  使用時機：當用戶說「分析 AAPL」「深度報告」「跑 Layer 3」「幫我看這支股票」「deep analysis」「產出報告」。
  包含 7 組分析模板（AI白話摘要/估值/體質/成長/風險/同業/決策摘要），輸出 JSON + Markdown 雙軌報告。
argument-hint: "[TICKER ...]"
allowed-tools: Bash, Read, Glob, Grep
---

# 深度分析 SOP（Layer 3 深度分析）

## 流程

### Step 1: 確認分析標的

確認要分析的股票 ticker：
- 如果用戶指定了 ticker（如 `$ARGUMENTS`），直接使用
- 如果從 `/scan-market` 銜接過來，使用通過篩選的清單
- 如果都沒有，詢問用戶要分析哪些股票

支援多支股票，逐支處理。

### Step 2: 抓取深度數據

對每支股票：

**方式 A — MCP 工具（優先）：**

呼叫 `fetch_deep_analysis` 工具：
- `ticker`: 股票代碼（如 "AAPL"）
- `force_refresh`: false（預設使用 24h 快取）

回傳結果包含：
- 估值倍數（EV/EBITDA, P/E, P/B, 分析師目標價）
- 財務體質（3-5 年歷史、資產負債表、現金流）
- 成長動能（EPS/營收預估、盈餘驚喜）
- 風險指標（Beta、放空比率、內部交易）
- 同業比較（5+ 同業排名）

**方式 B — CLI 備援（MCP 不可用時）：**

```bash
# 指定股票
uv run python -m scripts.analyzer.run_layer3 --tickers AAPL MSFT

# 從 Layer 1 結果自動載入
uv run python -m scripts.analyzer.run_layer3 --from-layer1

# 強制重新抓取
uv run python -m scripts.analyzer.run_layer3 --tickers AAPL --force-refresh
```

### Step 3: 生成分析報告

**方式 A — MCP 工具（優先）：**

呼叫 `generate_analysis_report` 工具：
- `ticker`: 股票代碼
- `force_refresh`: false
- `ai_summary`: true（預設生成 AI 白話摘要，需 GEMINI_API_KEY）
- `include_chart`: true（預設生成 6 個月價格走勢圖）

**方式 B — CLI 備援：**

報告由 CLI 自動生成，存至 `data/reports/` 目錄。

### Step 4: 呈現結果

**首先呈現 T0 白話分析摘要（如有）：**

AI 自動生成的白話文解讀，讓非財金背景的用戶也能快速理解。

**然後呈現 T6 投資決策摘要：**

四維評估概覽：
- 估值面：[評分/摘要]
- 體質面：[評分/摘要]
- 成長面：[評分/摘要]
- 風險面：[評分/摘要]

**然後詢問用戶：**

> 「要查看哪個模板的完整報告？」
> - T1 價值估值報告 — 價格走勢圖、DCF 參數、估值倍數、分析師目標價
> - T2 財務體質檢查 — 三表摘要、資產負債表、現金流趨勢
> - T3 成長動能分析 — 營收/盈餘成長、EPS 預估、盈餘驚喜
> - T4 風險與情境分析 — 波動性、放空比率、內部交易、機構持股
> - T5 同業競爭力排名 — 5+ 同業全面對比、各指標排名
> - 全部顯示

### Step 5: 告知存檔位置

> 「報告已存至：」
> - JSON: `data/deep_analysis_AAPL_YYYYMMDD.json`
> - Markdown: `data/reports/deep_analysis_AAPL_YYYYMMDD.md`

## 批次處理指引

- 每支股票約 4 秒（12 個 yfinance API 呼叫）
- 15 支股票約 60 秒
- 逐支處理，每支完成後立即呈現 T6 摘要
- 全部完成後提供總覽比較

## 錯誤處理

| 情況 | 處理方式 |
|------|---------|
| 單支抓取失敗 | 跳過並告知用戶，繼續處理下一支 |
| 同業比較失敗 | 不影響主要分析，T5 報告標註「資料不足」 |
| 全部失敗 | 建議檢查網路連線或稍後重試 |
| 快取過期 | 自動重新抓取（預設 24h TTL） |
| MCP 工具不可用 | 改用 CLI 備援指令 |

## 快取說明

- 深度分析快取：`data/deep_analysis_cache.json`，TTL 24 小時
- `force_refresh=True` 或 `--force-refresh` 強制更新
- 失敗的抓取 1 小時後自動重試

## 參考檔案

- 深度數據抓取：`scripts/analyzer/deep_data_fetcher.py`
- 同業比較器：`scripts/analyzer/peer_finder.py`
- AI 白話摘要：`scripts/analyzer/ai_summarizer.py`（Gemini API, Flash）
- 價格走勢圖：`scripts/analyzer/price_chart.py`（matplotlib PNG）
- 報告生成器：`scripts/analyzer/report_generator.py`（7 組模板 T0-T6）
- CLI 進入點：`scripts/analyzer/run_layer3.py`（`--no-ai-summary`、`--no-chart` 可停用）
- MCP 工具：`mcp_servers/financial_tools.py`（fetch_deep_analysis, generate_analysis_report）
