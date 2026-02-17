/**
 * TypeScript 型別定義 — 映射 Python dataclass to_dict() 輸出。
 */

// ============================================================
// Layer 1 篩選結果
// ============================================================

export interface TickerMetrics {
	trailing_pe: number | null;
	peg_ratio: number | null;
	roe: number | null;
	debt_to_equity: number | null;
	trailing_eps: number | null;
	book_value: number | null;
	sector: string | null;
	industry: string | null;
	company_name: string | null;
}

export interface SectorPercentiles {
	pe_percentile: number | null;
	peg_percentile: number | null;
	roe_percentile: number | null;
	de_percentile: number | null;
	sector: string;
	sector_count: number;
}

export interface ScreeningResult {
	symbol: string;
	passed: boolean;
	screening_mode: string;
	graham_number: number | null;
	current_price: number | null;
	margin_of_safety_pct: number | null;
	fail_reasons: string[];
	sector_percentiles: SectorPercentiles | null;
	passed_sector_filter: boolean;
	passed_safety_filter: boolean;
	safety_fail_reasons: string[];
	metrics: TickerMetrics;
}

export interface ScreeningPayload {
	timestamp: string;
	tag: string;
	screening_mode: string;
	total_screened: number;
	total_passed: number;
	results: ScreeningResult[];
}

// ============================================================
// Layer 3 深度分析
// ============================================================

export interface ValuationData {
	ev_to_ebitda: number | null;
	ev_to_revenue: number | null;
	price_to_book: number | null;
	price_to_sales: number | null;
	trailing_pe: number | null;
	forward_pe: number | null;
	target_price_mean: number | null;
	target_price_median: number | null;
	target_price_high: number | null;
	target_price_low: number | null;
	analyst_count: number | null;
	recommendation_key: string | null;
	recommendation_mean: number | null;
	recommendations_summary: Record<string, number> | null;
	free_cashflow: number | null;
	free_cashflow_history: Record<string, number>;
	beta: number | null;
	enterprise_value: number | null;
	dividend_yield: number | null;
	payout_ratio: number | null;
}

export interface FinancialHealthData {
	revenue_history: Record<string, number>;
	net_income_history: Record<string, number>;
	ebitda_history: Record<string, number>;
	gross_margin_history: Record<string, number>;
	operating_margin_history: Record<string, number>;
	total_assets: number | null;
	total_liabilities: number | null;
	total_equity: number | null;
	total_debt: number | null;
	total_cash: number | null;
	current_ratio: number | null;
	quick_ratio: number | null;
	working_capital: number | null;
	operating_cashflow_history: Record<string, number>;
	capex_history: Record<string, number>;
	free_cashflow_history: Record<string, number>;
}

export interface EpsEstimate {
	period: string;
	avg: number | null;
	low: number | null;
	high: number | null;
	yearAgoEps: number | null;
	numberOfAnalysts: number | null;
	growth: number | null;
}

export interface RevenueEstimate {
	period: string;
	avg: number | null;
	low: number | null;
	high: number | null;
	numberOfAnalysts: number | null;
	yearAgoRevenue: number | null;
	growth: number | null;
}

export interface EarningsSurprise {
	date: string;
	estimate: number | null;
	actual: number | null;
	surprise_pct: number | null;
}

export interface GrowthMomentumData {
	eps_estimates: EpsEstimate[];
	revenue_estimates: RevenueEstimate[];
	earnings_surprises: EarningsSurprise[];
	revenue_growth: number | null;
	earnings_growth: number | null;
	earnings_quarterly_growth: number | null;
}

export interface InsiderTransaction {
	insider: string;
	position: string;
	transaction: string;
	shares: number | null;
	value: number | null;
	date: string;
}

export interface InstitutionalHolder {
	holder: string;
	pct_held: number | null;
	shares: number | null;
	value: number | null;
}

export interface RiskMetricsData {
	beta: number | null;
	short_ratio: number | null;
	short_percent_of_float: number | null;
	fifty_two_week_high: number | null;
	fifty_two_week_low: number | null;
	fifty_two_week_change: number | null;
	current_price: number | null;
	held_percent_insiders: number | null;
	held_percent_institutions: number | null;
	insider_transactions: InsiderTransaction[];
	top_institutional_holders: InstitutionalHolder[];
}

export interface PeerMetrics {
	symbol: string;
	name: string;
	pe: number | null;
	forward_pe: number | null;
	ev_ebitda: number | null;
	ev_revenue: number | null;
	price_to_book: number | null;
	roe: number | null;
	gross_margin: number | null;
	operating_margin: number | null;
	profit_margin: number | null;
	revenue_growth: number | null;
	earnings_growth: number | null;
	market_cap: number | null;
	beta: number | null;
	dividend_yield: number | null;
	debt_to_equity: number | null;
}

export interface PeerComparisonData {
	peers: PeerMetrics[];
	sector: string;
	industry: string;
	rank_in_peers: Record<string, number>;
}

export interface DeepAnalysisData {
	symbol: string;
	company_name: string;
	sector: string;
	industry: string;
	market_cap: number | null;
	current_price: number | null;
	currency: string;
	graham_number: number | null;
	margin_of_safety_pct: number | null;
	valuation: ValuationData;
	financial_health: FinancialHealthData;
	growth_momentum: GrowthMomentumData;
	risk_metrics: RiskMetricsData;
	peer_comparison: PeerComparisonData;
	fetched_at: string;
	data_quality_score: number;
}
