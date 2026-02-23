"""
價格走勢圖生成器

使用 yfinance 取得歷史價格數據，
用 matplotlib 生成 PNG 圖表供報告嵌入。
"""

import logging
from datetime import datetime
from pathlib import Path

import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_price_history(
    symbol: str,
    period: str = "6mo",
) -> dict:
    """
    透過 yfinance 抓取股價歷史數據。

    Args:
        symbol: 股票代碼
        period: 時間範圍（預設 6 個月）

    Returns:
        {"dates": [str, ...], "closes": [float, ...]}，失敗時回傳空 dict
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)

        if hist.empty:
            logger.warning(f"{symbol} 無價格歷史數據")
            return {}

        dates = [d.strftime("%Y-%m-%d") for d in hist.index]
        closes = [round(float(c), 2) for c in hist["Close"]]

        logger.info(f"{symbol} 取得 {len(dates)} 筆價格數據")
        return {"dates": dates, "closes": closes}

    except Exception as e:
        logger.warning(f"{symbol} 價格歷史抓取失敗: {e}")
        return {}


def generate_price_chart(
    symbol: str,
    company_name: str,
    price_history: dict,
    output_dir: Path,
) -> str | None:
    """
    生成 6 個月價格走勢圖 PNG。

    Args:
        symbol: 股票代碼
        company_name: 公司名稱
        price_history: {"dates": [...], "closes": [...]}
        output_dir: 報告根目錄（圖表存至 output_dir/charts/）

    Returns:
        圖表相對路徑（相對於 output_dir），失敗時回傳 None
    """
    if not price_history or not price_history.get("dates"):
        logger.warning(f"{symbol} 無價格數據，跳過圖表生成")
        return None

    try:
        import matplotlib
        matplotlib.use("Agg")  # 非互動式後端
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from datetime import datetime as dt

        # 嘗試設定支援中文的字體
        import warnings
        warnings.filterwarnings("ignore", message="Glyph .* missing from")
        try:
            from matplotlib.font_manager import FontProperties
            for font_name in ["Microsoft JhengHei", "Microsoft YaHei", "SimHei", "Arial Unicode MS"]:
                try:
                    fp = FontProperties(family=font_name)
                    if fp.get_name() != font_name:
                        continue
                    matplotlib.rcParams["font.sans-serif"] = [font_name] + matplotlib.rcParams.get("font.sans-serif", [])
                    matplotlib.rcParams["axes.unicode_minus"] = False
                    break
                except Exception:
                    continue
        except Exception:
            pass

        dates_str = price_history["dates"]
        closes = price_history["closes"]
        dates = [dt.strptime(d, "%Y-%m-%d") for d in dates_str]

        # 深色主題
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(10, 4), dpi=100)

        # 折線圖
        ax.plot(dates, closes, color="#00BFFF", linewidth=1.5, zorder=5)

        # 填充區域
        ax.fill_between(dates, closes, alpha=0.15, color="#00BFFF")

        # 標記最高價、最低價、當前價
        max_idx = closes.index(max(closes))
        min_idx = closes.index(min(closes))

        ax.scatter(
            [dates[max_idx]], [closes[max_idx]],
            color="#00FF7F", s=60, zorder=10, label=f"最高 ${closes[max_idx]:.2f}",
        )
        ax.scatter(
            [dates[min_idx]], [closes[min_idx]],
            color="#FF6347", s=60, zorder=10, label=f"最低 ${closes[min_idx]:.2f}",
        )
        ax.scatter(
            [dates[-1]], [closes[-1]],
            color="#FFD700", s=60, zorder=10, label=f"當前 ${closes[-1]:.2f}",
        )

        # 標註文字
        ax.annotate(
            f"${closes[max_idx]:.2f}",
            (dates[max_idx], closes[max_idx]),
            textcoords="offset points", xytext=(0, 12),
            fontsize=9, color="#00FF7F", ha="center",
        )
        ax.annotate(
            f"${closes[min_idx]:.2f}",
            (dates[min_idx], closes[min_idx]),
            textcoords="offset points", xytext=(0, -15),
            fontsize=9, color="#FF6347", ha="center",
        )

        # 格式設定
        ax.set_title(
            f"{symbol} 近 6 個月股價走勢",
            fontsize=14, color="white", pad=12,
        )
        ax.set_ylabel("USD ($)", fontsize=10, color="gray")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.tick_params(colors="gray", labelsize=9)
        ax.grid(axis="y", alpha=0.2, color="gray")
        ax.legend(
            loc="upper left", fontsize=8,
            facecolor="#1a1a2e", edgecolor="gray",
        )

        # Y 軸留白
        price_range = max(closes) - min(closes)
        padding = max(price_range * 0.1, 1.0)
        ax.set_ylim(min(closes) - padding, max(closes) + padding)

        fig.tight_layout()

        # 存檔
        charts_dir = output_dir / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"price_chart_{symbol}_{date_str}.png"
        filepath = charts_dir / filename

        fig.savefig(filepath, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)

        relative_path = f"charts/{filename}"
        logger.info(f"{symbol} 價格走勢圖已存至 {filepath}")
        return relative_path

    except Exception as e:
        logger.warning(f"{symbol} 價格走勢圖生成失敗: {e}")
        return None
