---
name: scan-market
description: >
  市場篩選 SOP — 從 S&P 1500 中篩選被低估的股票。
  使用時機：當用戶說「掃描市場」「篩選低估股」「跑 Layer 1」「幫我找被低估的股票」「scan market」「市場掃描」。
  執行雙軌制篩選（產業相對排名 + 安全底線過濾），輸出通過篩選的股票清單。
allowed-tools: Bash, Read, Glob, Grep
---

# 市場篩選 SOP（Layer 1 量化篩選）

## 流程

### Step 1: 確認篩選範圍

詢問用戶要篩選的 universe，提供選項：
- **sp1500**（預設）— S&P 1500 全市場，約 1500 支
- **sp500** — S&P 500 大型股，約 500 支
- **sp400** — S&P 400 中型股
- **sp600** — S&P 600 小型股

如果用戶沒有特別指定，使用 **sp1500**。

### Step 2: 執行篩選

**方式 A — MCP 工具（優先）：**

呼叫 `run_sector_screening` 工具：
- `universe`: 用戶選擇的 universe（預設 "sp1500"）
- `percentile_threshold`: 0.30（預設，top 30%）

**方式 B — CLI 備援（MCP 不可用時）：**

```bash
uv run python -m scripts.scanner.run_layer1 --universe sp1500 --mode dual
```

如需強制重新抓取：
```bash
uv run python -m scripts.scanner.run_layer1 --universe sp1500 --mode dual --force-refresh
```

### Step 3: 整理並呈現結果

從回傳結果中提取以下資訊：

**摘要：**
> 篩選完成：X / Y 通過（Z% 通過率）

**產業分布表格：**

| 產業 | 通過 | 篩選總數 |
|------|------|---------|
| Technology | 3 | 85 |
| ... | ... | ... |

**通過股票清單：**

| Symbol | 產業 | PE | PEG | ROE | D/E | Graham Number | MOS% |
|--------|------|-----|-----|-----|-----|--------------|------|
| AAPL | Technology | 28.5 | 1.2 | 45% | 1.8 | $125.00 | 15.3% |
| ... | ... | ... | ... | ... | ... | ... | ... |

### Step 4: 銜接深度分析

呈現結果後，詢問用戶：

> 「以上是通過篩選的股票。要對哪些進行深度分析？」
> - 全部分析
> - 選擇特定股票（如：AAPL, MSFT）
> - 不需要，到此為止

如果用戶選擇分析，使用 `/deep-analysis` 的流程繼續。

## 錯誤處理

| 情況 | 處理方式 |
|------|---------|
| API 限流 | 建議使用 `--delay 0.3` 或等待後重試 |
| 網路失敗 | 檢查是否有近期快取結果：讀取 `data/screening_*.json` |
| 無股票通過 | 告知用戶，建議放寬門檻（調高 percentile_threshold 到 0.40） |
| MCP 工具不可用 | 改用 CLI 備援指令 |

## 快取說明

- 指標快取位於 `data/metrics_cache.json`，TTL 24 小時
- 失敗的抓取快取 1 小時後自動重試
- 使用 `--force-refresh` 可忽略所有快取

## 參考檔案

- 篩選設定：`scripts/scanner/config.py`
- 篩選邏輯：`scripts/scanner/sector_screener.py`
- CLI 進入點：`scripts/scanner/run_layer1.py`
- 結果儲存：`scripts/scanner/results_store.py`
