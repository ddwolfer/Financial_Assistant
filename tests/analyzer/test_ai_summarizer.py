"""
AI 白話摘要生成器測試。

測試 AISummaryConfig、generate_ai_summary_sync、render_t0_ai_summary。
"""

import os
from unittest.mock import patch, MagicMock

import pytest

from scripts.analyzer.ai_summarizer import (
    AISummaryConfig,
    DEFAULT_AI_SUMMARY_CONFIG,
    generate_ai_summary_sync,
    render_t0_ai_summary,
)


# ============================================================
# AISummaryConfig 測試
# ============================================================

class TestAISummaryConfig:
    """AISummaryConfig dataclass 測試。"""

    def test_default_values(self):
        """預設值應正確設定。"""
        config = AISummaryConfig()
        assert config.enabled is True
        assert "flash" in config.primary_model
        assert config.max_tokens == 8192
        assert config.temperature == 0.3
        assert config.timeout_seconds == 60.0

    def test_frozen_immutable(self):
        """Config 應為不可變（frozen）。"""
        config = AISummaryConfig()
        with pytest.raises(AttributeError):
            config.enabled = False

    def test_custom_values(self):
        """應能以自訂值建立。"""
        config = AISummaryConfig(
            enabled=False,
            primary_model="test-model",
            max_tokens=1024,
        )
        assert config.enabled is False
        assert config.primary_model == "test-model"
        assert config.max_tokens == 1024

    def test_default_config_singleton(self):
        """DEFAULT_AI_SUMMARY_CONFIG 應為有效的 AISummaryConfig。"""
        assert isinstance(DEFAULT_AI_SUMMARY_CONFIG, AISummaryConfig)
        assert DEFAULT_AI_SUMMARY_CONFIG.enabled is True


# ============================================================
# generate_ai_summary_sync 測試
# ============================================================

class TestGenerateAiSummarySync:
    """generate_ai_summary_sync 函數測試。"""

    def test_no_api_key_returns_none(self):
        """未設定 GEMINI_API_KEY 應回傳 None。"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GEMINI_API_KEY", None)
            result = generate_ai_summary_sync(
                report_markdown="test report",
                symbol="AAPL",
                company_name="Apple Inc.",
            )
            assert result is None

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch("scripts.analyzer.ai_summarizer.genai")
    def test_successful_generation(self, mock_genai):
        """成功呼叫 API 應回傳摘要文字。"""
        # 設定 mock
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "這是一段白話摘要。"
        mock_client.models.generate_content.return_value = mock_response

        result = generate_ai_summary_sync(
            report_markdown="## T1: 價值估值報告\n| P/E | 15x |",
            symbol="AAPL",
            company_name="Apple Inc.",
        )
        assert result == "這是一段白話摘要。"
        mock_client.models.generate_content.assert_called_once()

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch("scripts.analyzer.ai_summarizer.genai")
    def test_primary_fails_fallback_succeeds(self, mock_genai):
        """主要模型失敗時應切換到備援模型。"""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        # 第一次呼叫（Flash）失敗，第二次成功
        mock_response = MagicMock()
        mock_response.text = "備援模型的摘要。"
        mock_client.models.generate_content.side_effect = [
            Exception("Flash 連線逾時"),
            mock_response,
        ]

        result = generate_ai_summary_sync(
            report_markdown="test",
            symbol="TEST",
            company_name="Test Corp",
        )
        assert result == "備援模型的摘要。"
        assert mock_client.models.generate_content.call_count == 2

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch("scripts.analyzer.ai_summarizer.genai")
    def test_all_models_fail_returns_none(self, mock_genai):
        """所有模型都失敗應回傳 None。"""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("全部失敗")

        result = generate_ai_summary_sync(
            report_markdown="test",
            symbol="TEST",
            company_name="Test Corp",
        )
        assert result is None
        assert mock_client.models.generate_content.call_count == 2

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    @patch("scripts.analyzer.ai_summarizer.genai")
    def test_api_key_passed_to_client(self, mock_genai):
        """GEMINI_API_KEY 應傳遞給 Client。"""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_client.models.generate_content.return_value = mock_response

        generate_ai_summary_sync(
            report_markdown="test",
            symbol="TEST",
            company_name="Test",
        )

        mock_genai.Client.assert_called_with(api_key="test-key")


# ============================================================
# render_t0_ai_summary 測試
# ============================================================

class TestRenderT0AiSummary:
    """render_t0_ai_summary 函數測試。"""

    def test_none_input_returns_none(self):
        """summary_text 為 None 時應回傳 None。"""
        result = render_t0_ai_summary(
            summary_text=None,
            symbol="AAPL",
            company_name="Apple Inc.",
        )
        assert result is None

    def test_renders_markdown_with_title(self):
        """應渲染包含 T0 標題的 Markdown。"""
        result = render_t0_ai_summary(
            summary_text="這是白話摘要。",
            symbol="AAPL",
            company_name="Apple Inc.",
        )
        assert "## T0: 白話分析摘要" in result
        assert "Apple Inc." in result
        assert "AAPL" in result

    def test_renders_summary_text(self):
        """應包含摘要文字內容。"""
        text = "蘋果公司是全球最大的科技公司之一。"
        result = render_t0_ai_summary(
            summary_text=text,
            symbol="AAPL",
            company_name="Apple Inc.",
        )
        assert text in result

    def test_renders_disclaimer(self):
        """應包含 AI 免責聲明。"""
        result = render_t0_ai_summary(
            summary_text="摘要。",
            symbol="AAPL",
            company_name="Apple Inc.",
        )
        assert "AI 自動生成" in result
        assert "不構成投資建議" in result

    def test_ends_with_separator(self):
        """應以分隔線結尾。"""
        result = render_t0_ai_summary(
            summary_text="摘要。",
            symbol="TEST",
            company_name="Test",
        )
        assert result.strip().endswith("---")
