/**
 * 格式化工具函式。
 */

/** 千分位格式化整數 */
export function formatNumber(value: number | null | undefined): string {
	if (value == null) return '—';
	return value.toLocaleString('en-US', { maximumFractionDigits: 0 });
}

/** 格式化為百分比（自動乘 100 若 |value| <= 1，否則直接顯示） */
export function formatPercent(value: number | null | undefined, multiply = false): string {
	if (value == null) return '—';
	const v = multiply ? value * 100 : value;
	return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
}

/** 格式化百分比（不帶正號） */
export function formatPercentPlain(value: number | null | undefined, multiply = false): string {
	if (value == null) return '—';
	const v = multiply ? value * 100 : value;
	return `${v.toFixed(2)}%`;
}

/** 格式化小數（保留指定位數） */
export function formatDecimal(value: number | null | undefined, digits = 2): string {
	if (value == null) return '—';
	return value.toFixed(digits);
}

/** 格式化貨幣（美元） */
export function formatCurrency(value: number | null | undefined): string {
	if (value == null) return '—';
	return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/** 格式化大數字（B/M/K） */
export function formatLargeNumber(value: number | null | undefined): string {
	if (value == null) return '—';
	const abs = Math.abs(value);
	if (abs >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
	if (abs >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
	if (abs >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
	if (abs >= 1e3) return `$${(value / 1e3).toFixed(1)}K`;
	return `$${value.toFixed(0)}`;
}

/** 正面/負面 CSS 類別 */
export function valueColor(value: number | null | undefined): string {
	if (value == null) return 'text-[#8b8fa3]';
	if (value > 0) return 'text-[#22c55e]';
	if (value < 0) return 'text-[#ef4444]';
	return 'text-[#e4e7ec]';
}

/** 將 history dict 的年份排序 */
export function sortedYears(history: Record<string, number> | null | undefined): string[] {
	if (!history) return [];
	return Object.keys(history).sort();
}
