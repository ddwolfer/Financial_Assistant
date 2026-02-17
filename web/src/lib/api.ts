/**
 * API 存取封裝 — 向 FastAPI 後端發送請求。
 *
 * SvelteKit 的 load 函式必須使用 event.fetch（支援相對 URL + SSR），
 * 因此所有 API 函式都接受可選的 fetch 參數。
 */

import type { ScreeningPayload, DeepAnalysisData } from './types';

type FetchFn = typeof globalThis.fetch;

const BASE = '/api';

async function fetchJson<T>(path: string, fetchFn: FetchFn = globalThis.fetch): Promise<T> {
	const res = await fetchFn(`${BASE}${path}`);
	if (!res.ok) {
		throw new Error(`API 錯誤: ${res.status} ${res.statusText}`);
	}
	return res.json();
}

/** 取得最新篩選結果 */
export function getLatestScreening(tag = 'layer1_dual', fetchFn?: FetchFn): Promise<ScreeningPayload> {
	return fetchJson(`/screening/latest?tag=${encodeURIComponent(tag)}`, fetchFn);
}

/** 列出所有篩選結果檔案 */
export function listScreeningFiles(fetchFn?: FetchFn): Promise<{ files: { filename: string; tag: string; size_bytes: number }[] }> {
	return fetchJson('/screening/list', fetchFn);
}

/** 取得已分析的股票代碼列表 */
export function getDeepAnalysisSymbols(fetchFn?: FetchFn): Promise<{ symbols: string[]; count: number }> {
	return fetchJson('/deep-analysis/symbols', fetchFn);
}

/** 取得指定股票的深度分析結果 */
export function getDeepAnalysis(symbol: string, fetchFn?: FetchFn): Promise<DeepAnalysisData> {
	return fetchJson(`/deep-analysis/${encodeURIComponent(symbol.toUpperCase())}`, fetchFn);
}

/** 取得指定股票的 Markdown 報告 */
export function getDeepAnalysisReport(symbol: string, fetchFn?: FetchFn): Promise<{ symbol: string; markdown: string }> {
	return fetchJson(`/deep-analysis/${encodeURIComponent(symbol.toUpperCase())}/report`, fetchFn);
}
