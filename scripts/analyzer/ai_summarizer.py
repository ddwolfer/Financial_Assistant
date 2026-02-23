"""
AI 白話分析摘要生成器

使用 Google Gemini API 將專業金融分析報告轉化為
一般人容易理解的繁體中文白話文摘要。
"""

import os
import logging
from dataclasses import dataclass

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AISummaryConfig:
    """AI 摘要生成器設定"""

    enabled: bool = True
    primary_model: str = "gemini-2.5-flash"
    fallback_model: str = "gemini-3-flash-preview"
    max_tokens: int = 8192
    temperature: float = 0.3
    timeout_seconds: float = 60.0


# 預設設定
DEFAULT_AI_SUMMARY_CONFIG = AISummaryConfig()

# 系統提示詞
_SYSTEM_PROMPT = """你是一位金融分析通譯師，專門將專業投資報告翻譯成一般人都能理解的白話文。

你的讀者不具備金融背景，需要你用日常生活的比喻和淺顯的語言來解釋。

請根據提供的分析報告，撰寫一段 800-1200 字的繁體中文白話分析摘要，涵蓋以下面向：

1. **這家公司在做什麼？**（用一句話說明主業）
2. **股價貴不貴？**（P/E、分析師目標價代表什麼意思）
3. **公司賺不賺錢？**（營收、淨利趨勢用白話解釋）
4. **未來有沒有成長空間？**（成長率、EPS 預估白話解讀）
5. **主要風險是什麼？**（Beta、放空比率、內部交易用生活化比喻）
6. **跟同業比起來如何？**（排名的意義）
7. **總結：值不值得關注？**（綜合以上給出直觀建議）

風格要求：
- 使用繁體中文
- 語氣親切、像朋友聊天一樣解釋
- 遇到專業術語時，先用括號給出白話解釋
- 適度使用生活化比喻讓數字有感
- 不要使用 Markdown 格式（純文字段落）
- 最後加一句簡短的風險提醒"""


def generate_ai_summary_sync(
    report_markdown: str,
    symbol: str,
    company_name: str,
    config: AISummaryConfig = DEFAULT_AI_SUMMARY_CONFIG,
) -> str | None:
    """
    呼叫 Google Gemini API 生成白話文分析摘要。

    Args:
        report_markdown: 完整的 T1-T6 Markdown 報告內容
        symbol: 股票代碼
        company_name: 公司名稱
        config: AI 摘要設定

    Returns:
        白話文摘要字串，失敗時回傳 None
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("未設定 GEMINI_API_KEY 環境變數，跳過 AI 白話摘要")
        return None

    user_message = (
        f"以下是 {company_name} ({symbol}) 的完整分析報告，"
        f"請用白話文為我解讀：\n\n{report_markdown}"
    )

    # 嘗試主要模型，失敗後切換備援模型
    models_to_try = [config.primary_model, config.fallback_model]

    for model_name in models_to_try:
        try:
            logger.info(f"使用 {model_name} 生成 {symbol} 白話摘要...")
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM_PROMPT,
                    max_output_tokens=config.max_tokens,
                    temperature=config.temperature,
                    http_options=types.HttpOptions(
                        timeout=int(config.timeout_seconds * 1000),
                    ),
                ),
            )
            summary_text = response.text
            logger.info(
                f"{symbol} 白話摘要生成完成 (模型: {model_name}, "
                f"字數: {len(summary_text)})"
            )
            return summary_text

        except Exception as e:
            logger.warning(f"{model_name} 生成 {symbol} 白話摘要失敗: {e}")
            continue

    logger.error(f"所有模型均無法生成 {symbol} 白話摘要")
    return None


def render_t0_ai_summary(
    summary_text: str | None,
    symbol: str,
    company_name: str,
) -> str | None:
    """
    渲染 T0 白話分析摘要 Markdown 段落。

    Args:
        summary_text: AI 生成的白話摘要文字，None 時跳過
        symbol: 股票代碼
        company_name: 公司名稱

    Returns:
        Markdown 格式的 T0 段落，輸入為 None 時回傳 None
    """
    if summary_text is None:
        return None

    lines = [
        f"## T0: 白話分析摘要 — {company_name} ({symbol})",
        "",
        summary_text,
        "",
        "> 以上摘要由 AI 自動生成，僅供參考，不構成投資建議。"
        " 請務必自行研究或諮詢專業人士後再做投資決策。",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)
