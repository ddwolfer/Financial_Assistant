# 數據篩選漏斗規格 (The Funnel)

## 第一層：量化硬指標篩選 (Quantitative Filter)
- **對象**: 全市場股票 (如 S&P 500, Russell 3000) 或指定的 Crypto 列表。
- **指標**: 
    - **價值指標**: $P/E Ratio < 15$ 或低於產業平均。
    - **增長指標**: $PEG Ratio < 1$。
    - **體質指標**: $ROE > 15\%$ 且 $Debt/Equity < 0.5$。
- **公式**: 使用 Graham Number 做為安全邊際參考：
  $$\text{Graham Number} = \sqrt{22.5 \times \text{EPS} \times \text{Book Value per Share}}$$

## 第二層：注意力與情緒篩選 (Attention/Sentiment)
- **目標**: 識別「熱門股 (MAG7)」與「冷門潛力股」。
- **邏輯**:
    - **熱門度計算**: 抓取近 24 小時新聞量與 Reddit/Twitter 提及次數。
    - **分類器**:
        - **High Attention**: 討論量前 5% -> 進入「市場領導者分析」。
        - **Low Attention**: 財務數據優異但討論量低於平均 -> 進入「隱藏價值股分析」。

## 第三層：深度數據抓取 (Deep Data Fetching)
- 針對過濾後剩餘的 10-20 檔標的，抓取完整的 10-K/10-Q 數據、WACC 參數以及至少 5 家同業對標數據。