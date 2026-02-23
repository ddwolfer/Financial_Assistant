---
name: analyze-mag7
description: >
  MAG7 科技巨頭分析 SOP — 對七大科技股執行完整深度分析。
  使用時機：當用戶說「跑 MAG7」「分析科技巨頭」「MAG7 報告」「analyze mag7」「七大科技股」「大盤龍頭分析」。
  自動對 AAPL/MSFT/GOOGL/AMZN/NVDA/META/TSLA 產出 7 組分析報告。
argument-hint: "[--force-refresh] [--no-ai-summary] [--no-chart]"
allowed-tools: Bash, Read, Glob, Grep
---

# MAG7 科技巨頭分析 SOP

## MAG7 固定清單

AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA

## 流程

### Step 1: 確認分析參數

預設直接執行，除非用戶指定：
- `--force-refresh`：強制重新抓取（忽略 24h 快取）
- `--no-ai-summary`：停用 AI 白話摘要
- `--no-chart`：停用價格走勢圖

如果用戶沒有特別指定，**使用預設值**（含 AI 摘要 + 走勢圖 + 使用快取）。

### Step 2: 執行分析

```bash
uv run python -m scripts.analyzer.run_layer3 --tickers AAPL MSFT GOOGL AMZN NVDA META TSLA --universe sp500
```

如需強制重新抓取：
```bash
uv run python -m scripts.analyzer.run_layer3 --tickers AAPL MSFT GOOGL AMZN NVDA META TSLA --universe sp500 --force-refresh
```

預估時間：7 支 × ~35 秒（含 AI 摘要）≈ 4 分鐘

### Step 3: 呈現結果

**先呈現總覽比較表：**

從 CLI 輸出的摘要表格整理：

| 代碼 | 公司 | 現價 | 目標價 | 上行空間 | 推薦 | 品質 |
|------|------|------|--------|---------|------|------|
| AAPL | Apple Inc. | $XXX | $XXX | +X.X% | BUY | XX% |
| ... | ... | ... | ... | ... | ... | ... |

**然後呈現每支股票的 T0 白話摘要重點（1-2 句）。**

**最後詢問用戶：**

> 「MAG7 分析完成。要查看哪支股票的完整報告？」
> - 選擇特定股票
> - 全部顯示 T6 決策摘要
> - 不需要，到此為止

### Step 4: 告知存檔位置

> 「報告已存至：」
> - JSON: `data/deep_analysis_{TICKER}_YYYYMMDD.json`
> - Markdown: `data/reports/deep_analysis_{TICKER}_YYYYMMDD.md`
> - 走勢圖: `data/reports/charts/price_chart_{TICKER}_YYYYMMDD.png`

## 錯誤處理

| 情況 | 處理方式 |
|------|---------|
| 單支抓取失敗 | 跳過並告知用戶，繼續處理下一支 |
| AI 摘要失敗 | 不影響主要報告，T0 標註「摘要不可用」 |
| GEMINI_API_KEY 未設定 | 自動跳過 AI 摘要，其餘正常產出 |
| 全部失敗 | 建議檢查網路連線或稍後重試 |

## 參考檔案

- CLI 進入點：`scripts/analyzer/run_layer3.py`
- AI 白話摘要：`scripts/analyzer/ai_summarizer.py`（Gemini API）
- 價格走勢圖：`scripts/analyzer/price_chart.py`
- 報告生成器：`scripts/analyzer/report_generator.py`（7 組模板 T0-T6）
