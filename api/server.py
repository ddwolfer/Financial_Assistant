"""
Dashboard API 伺服器。

提供 REST API 端點供 Svelte 5 前端存取篩選結果與深度分析數據。
直接呼叫 results_store.py 現有函式，不重複實作檔案讀取邏輯。
"""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from scripts.scanner.results_store import (
    list_deep_analysis_symbols,
    load_latest_deep_analysis,
    load_latest_deep_analysis_report,
    load_latest_results,
)

app = FastAPI(title="Quant-Analyst Dashboard API", version="0.1.0")

# CORS — 開發環境允許 Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@app.get("/api/health")
def health_check():
    """健康檢查端點。"""
    return {"status": "ok"}


@app.get("/api/screening/latest")
def get_latest_screening(tag: str = "layer1_dual"):
    """取得指定 tag 的最新篩選結果。"""
    result = load_latest_results(tag=tag)
    if result is None:
        raise HTTPException(status_code=404, detail=f"找不到 tag={tag} 的篩選結果")
    return result


@app.get("/api/screening/list")
def list_screening_files():
    """列出所有篩選結果檔案。"""
    files = []
    for pattern in ["screening_layer1_*.json", "screening_layer1_dual_*.json"]:
        for f in sorted(_DATA_DIR.glob(pattern), reverse=True):
            files.append({
                "filename": f.name,
                "tag": "layer1_dual" if "dual" in f.name else "layer1",
                "size_bytes": f.stat().st_size,
            })
    return {"files": files}


@app.get("/api/deep-analysis/symbols")
def get_deep_analysis_symbols():
    """列出所有已有深度分析結果的股票代碼。"""
    symbols = list_deep_analysis_symbols()
    return {"symbols": symbols, "count": len(symbols)}


@app.get("/api/deep-analysis/{symbol}")
def get_deep_analysis(symbol: str):
    """取得指定股票最新的深度分析 JSON 結果。"""
    data = load_latest_deep_analysis(symbol=symbol.upper())
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"找不到 {symbol.upper()} 的深度分析結果",
        )
    return data


@app.get("/api/deep-analysis/{symbol}/report")
def get_deep_analysis_report(symbol: str):
    """取得指定股票最新的 Markdown 報告。"""
    report = load_latest_deep_analysis_report(symbol=symbol.upper())
    if report is None:
        raise HTTPException(
            status_code=404,
            detail=f"找不到 {symbol.upper()} 的分析報告",
        )
    return {"symbol": symbol.upper(), "markdown": report}
