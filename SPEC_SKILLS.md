# Claude Skills & MCP 整合規格

## 1. MCP Tools (Python 實作)
必須暴露給 Claude 的工具函數：
- `check_data_cache(ticker)`: 檢查本地 `data/` 是否已有最新財報。
- `fetch_missing_data(ticker)`: 啟動抓取腳本補齊數據。
- `calculate_financial_metrics(ticker)`: 預處理複雜公式 (如 WACC 拆解)。
- `send_tg_notification(message)`: 將分析摘要推送到 Telegram。

## 2. SKILL.md SOP 流程
定義在 `.claude/skills/finance_expert/SKILL.md`:
1. **偵測需求**: 用戶輸入 "分析 [Ticker]"。
2. **驗證數據**: 呼叫 `check_data_cache`。
3. **數據補齊循環**: 若無數據，呼叫 `fetch_missing_data` 直到回傳 Success。
4. **注入 Prompt**: 根據標的類型，從 `scripts/templates/` 選擇合適的分析模型。
5. **推理分析**: Claude 根據抓取到的數據，填充 12 組分析模板中的內容。