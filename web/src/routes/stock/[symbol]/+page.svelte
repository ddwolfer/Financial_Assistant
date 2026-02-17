<script lang="ts">
	import AnalysisTabs from '$lib/components/AnalysisTabs.svelte';
	import MetricsGrid from '$lib/components/MetricsGrid.svelte';
	import FinancialChart from '$lib/components/FinancialChart.svelte';
	import PeerTable from '$lib/components/PeerTable.svelte';
	import PeerRadar from '$lib/components/PeerRadar.svelte';
	import RecommendationBadge from '$lib/components/RecommendationBadge.svelte';
	import ChartCanvas from '$lib/components/ChartCanvas.svelte';
	import {
		formatCurrency, formatLargeNumber, formatDecimal, formatPercent,
		formatPercentPlain, formatNumber, valueColor, sortedYears,
	} from '$lib/utils';

	let { data } = $props();
	const a = $derived(data.analysis);

	let activeTab = $state('t6');

	const tabs = [
		{ id: 't6', label: '投資決策摘要' },
		{ id: 't1', label: '估值分析' },
		{ id: 't2', label: '財務體質' },
		{ id: 't3', label: '成長動能' },
		{ id: 't4', label: '風險分析' },
		{ id: 't5', label: '同業比較' },
	];

	// 目標價上漲空間
	const upside = $derived(
		a.valuation.target_price_mean && a.current_price
			? ((a.valuation.target_price_mean - a.current_price) / a.current_price) * 100
			: null
	);

	// 分析師推薦分布圖
	const recChartConfig = $derived.by(() => {
		const rec = a.valuation.recommendations_summary;
		if (!rec) return null;
		return {
			type: 'doughnut' as const,
			data: {
				labels: ['強力買入', '買入', '持有', '賣出', '強力賣出'],
				datasets: [{
					data: [rec.strongBuy ?? 0, rec.buy ?? 0, rec.hold ?? 0, rec.sell ?? 0, rec.strongSell ?? 0],
					backgroundColor: ['#22c55e', '#4ade80', '#f59e0b', '#f87171', '#ef4444'],
					borderColor: '#1a1d29',
					borderWidth: 2,
				}],
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: { position: 'bottom' as const, labels: { color: '#e4e7ec', font: { size: 11 } } },
				},
			},
		};
	});

	// 目標價範圍圖
	const targetPriceConfig = $derived.by(() => {
		const v = a.valuation;
		if (!v.target_price_low || !v.target_price_high) return null;
		return {
			type: 'bar' as const,
			data: {
				labels: ['目標價範圍'],
				datasets: [
					{ label: '最低', data: [v.target_price_low], backgroundColor: '#ef444480', borderColor: '#ef4444', borderWidth: 1 },
					{ label: '平均', data: [v.target_price_mean], backgroundColor: '#f59e0b80', borderColor: '#f59e0b', borderWidth: 1 },
					{ label: '中位數', data: [v.target_price_median], backgroundColor: '#3b82f680', borderColor: '#3b82f6', borderWidth: 1 },
					{ label: '最高', data: [v.target_price_high], backgroundColor: '#22c55e80', borderColor: '#22c55e', borderWidth: 1 },
					{ label: '現價', data: [a.current_price], backgroundColor: '#e4e7ec80', borderColor: '#e4e7ec', borderWidth: 1 },
				],
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				indexAxis: 'y' as const,
				plugins: { legend: { labels: { color: '#e4e7ec', font: { size: 11 } } } },
				scales: {
					x: { ticks: { color: '#8b8fa3', callback: (v: number) => `$${v}` }, grid: { color: '#2d3142' } },
					y: { display: false },
				},
			},
		};
	});

	// 盈餘驚喜圖
	const surpriseConfig = $derived.by(() => {
		const surprises = a.growth_momentum.earnings_surprises;
		if (!surprises || surprises.length === 0) return null;
		const sorted = [...surprises].sort((x, y) => x.date.localeCompare(y.date));
		return {
			type: 'bar' as const,
			data: {
				labels: sorted.map((s) => s.date.substring(0, 10)),
				datasets: [
					{ label: '預估 EPS', data: sorted.map((s) => s.estimate), backgroundColor: '#8b8fa380', borderColor: '#8b8fa3', borderWidth: 1 },
					{ label: '實際 EPS', data: sorted.map((s) => s.actual), backgroundColor: '#3b82f680', borderColor: '#3b82f6', borderWidth: 1 },
				],
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: { legend: { labels: { color: '#e4e7ec', font: { size: 11 } } } },
				scales: {
					x: { ticks: { color: '#8b8fa3', font: { size: 10 } }, grid: { color: '#2d3142' } },
					y: { ticks: { color: '#8b8fa3' }, grid: { color: '#2d3142' } },
				},
			},
		};
	});
</script>

<div class="space-y-6">
	<!-- 返回連結 -->
	<a href="/screening" class="text-sm text-[#3b82f6] hover:underline no-underline">← 返回篩選結果</a>

	<!-- 頂部摘要卡片 -->
	<div class="bg-[#1a1d29] border border-[#2d3142] rounded-lg p-6">
		<div class="flex items-start justify-between mb-4">
			<div>
				<h1 class="text-2xl font-bold text-[#e4e7ec]">{a.symbol}</h1>
				<p class="text-[#8b8fa3] text-sm">{a.company_name} · {a.sector} · {a.industry}</p>
			</div>
			<RecommendationBadge recommendation={a.valuation.recommendation_key} mean={a.valuation.recommendation_mean} />
		</div>

		<div class="grid grid-cols-6 gap-4">
			<div>
				<div class="text-[#8b8fa3] text-xs">現價</div>
				<div class="text-xl font-bold text-[#e4e7ec]">{formatCurrency(a.current_price)}</div>
			</div>
			<div>
				<div class="text-[#8b8fa3] text-xs">目標價（均值）</div>
				<div class="text-xl font-bold text-[#e4e7ec]">{formatCurrency(a.valuation.target_price_mean)}</div>
			</div>
			<div>
				<div class="text-[#8b8fa3] text-xs">上漲空間</div>
				<div class="text-xl font-bold {valueColor(upside)}">{formatPercent(upside)}</div>
			</div>
			<div>
				<div class="text-[#8b8fa3] text-xs">市值</div>
				<div class="text-xl font-bold text-[#e4e7ec]">{formatLargeNumber(a.market_cap)}</div>
			</div>
			<div>
				<div class="text-[#8b8fa3] text-xs">本益比 P/E</div>
				<div class="text-xl font-bold text-[#e4e7ec]">{formatDecimal(a.valuation.trailing_pe)}</div>
			</div>
			<div>
				<div class="text-[#8b8fa3] text-xs">資料品質</div>
				<div class="text-xl font-bold text-[#f59e0b]">{(a.data_quality_score * 100).toFixed(0)}%</div>
			</div>
		</div>
	</div>

	<!-- 分頁區 -->
	<AnalysisTabs {tabs} bind:activeTab>
		<!-- T6: 投資決策摘要 -->
		{#if activeTab === 't6'}
			<div class="grid grid-cols-2 gap-6">
				<!-- 四維評估 -->
				<div class="space-y-4">
					<h3 class="text-base font-semibold text-[#e4e7ec]">四維評估</h3>
					<MetricsGrid metrics={[
						{ label: '估值倍數 P/E', value: formatDecimal(a.valuation.trailing_pe), color: 'text-[#e4e7ec]' },
						{ label: '遠期 P/E', value: formatDecimal(a.valuation.forward_pe), color: 'text-[#e4e7ec]' },
						{ label: 'EV/EBITDA', value: formatDecimal(a.valuation.ev_to_ebitda), color: 'text-[#e4e7ec]' },
						{ label: '葛拉漢數', value: formatCurrency(a.graham_number), color: 'text-[#e4e7ec]' },
						{ label: '流動比率', value: formatDecimal(a.financial_health.current_ratio), color: a.financial_health.current_ratio && a.financial_health.current_ratio >= 1 ? 'text-[#22c55e]' : 'text-[#ef4444]' },
						{ label: '負債/權益', value: formatDecimal(a.financial_health.total_debt && a.financial_health.total_equity ? a.financial_health.total_debt / a.financial_health.total_equity : null), color: 'text-[#e4e7ec]' },
						{ label: '營收成長', value: formatPercent(a.growth_momentum.revenue_growth, true), color: valueColor(a.growth_momentum.revenue_growth) },
						{ label: '盈餘成長', value: formatPercent(a.growth_momentum.earnings_growth, true), color: valueColor(a.growth_momentum.earnings_growth) },
						{ label: 'Beta', value: formatDecimal(a.risk_metrics.beta), color: 'text-[#e4e7ec]' },
						{ label: '放空比率', value: formatDecimal(a.risk_metrics.short_ratio), color: 'text-[#e4e7ec]' },
						{ label: '機構持股', value: formatPercentPlain(a.risk_metrics.held_percent_institutions, true), color: 'text-[#e4e7ec]' },
						{ label: '內部持股', value: formatPercentPlain(a.risk_metrics.held_percent_insiders, true), color: 'text-[#e4e7ec]' },
					]} columns={3} />
				</div>

				<!-- 分析師共識 -->
				<div class="space-y-4">
					<h3 class="text-base font-semibold text-[#e4e7ec]">分析師共識</h3>
					<MetricsGrid metrics={[
						{ label: '分析師人數', value: formatNumber(a.valuation.analyst_count ?? 0), color: 'text-[#e4e7ec]' },
						{ label: '目標價中位數', value: formatCurrency(a.valuation.target_price_median), color: 'text-[#e4e7ec]' },
						{ label: '目標價最高', value: formatCurrency(a.valuation.target_price_high), color: 'text-[#22c55e]' },
						{ label: '目標價最低', value: formatCurrency(a.valuation.target_price_low), color: 'text-[#ef4444]' },
					]} columns={2} />

					{#if recChartConfig}
						<ChartCanvas config={recChartConfig} height="200px" />
					{/if}
				</div>
			</div>

		<!-- T1: 估值分析 -->
		{:else if activeTab === 't1'}
			<div class="space-y-6">
				<h3 class="text-base font-semibold text-[#e4e7ec]">估值倍數</h3>
				<MetricsGrid metrics={[
					{ label: '本益比 P/E', value: formatDecimal(a.valuation.trailing_pe) },
					{ label: '遠期本益比', value: formatDecimal(a.valuation.forward_pe) },
					{ label: 'EV/EBITDA', value: formatDecimal(a.valuation.ev_to_ebitda) },
					{ label: 'EV/營收', value: formatDecimal(a.valuation.ev_to_revenue) },
					{ label: '股價淨值比 P/B', value: formatDecimal(a.valuation.price_to_book) },
					{ label: '股價營收比 P/S', value: formatDecimal(a.valuation.price_to_sales) },
					{ label: '殖利率', value: formatPercentPlain(a.valuation.dividend_yield, true) },
					{ label: '配息率', value: formatPercentPlain(a.valuation.payout_ratio, true) },
				]} />

				<div class="grid grid-cols-2 gap-6">
					<div>
						<h3 class="text-base font-semibold text-[#e4e7ec] mb-4">目標價範圍</h3>
						{#if targetPriceConfig}
							<ChartCanvas config={targetPriceConfig} height="200px" />
						{:else}
							<p class="text-[#8b8fa3] text-sm">無目標價資料</p>
						{/if}
					</div>
					<div>
						<h3 class="text-base font-semibold text-[#e4e7ec] mb-4">分析師推薦分布</h3>
						{#if recChartConfig}
							<ChartCanvas config={recChartConfig} height="200px" />
						{:else}
							<p class="text-[#8b8fa3] text-sm">無推薦資料</p>
						{/if}
					</div>
				</div>

				<h3 class="text-base font-semibold text-[#e4e7ec]">自由現金流趨勢</h3>
				<FinancialChart
					datasets={[
						{ label: '自由現金流', data: a.valuation.free_cashflow_history, color: '#3b82f6' },
					]}
				/>
			</div>

		<!-- T2: 財務體質 -->
		{:else if activeTab === 't2'}
			<div class="space-y-6">
				<h3 class="text-base font-semibold text-[#e4e7ec]">資產負債摘要</h3>
				<MetricsGrid metrics={[
					{ label: '總資產', value: formatLargeNumber(a.financial_health.total_assets) },
					{ label: '總負債', value: formatLargeNumber(a.financial_health.total_liabilities) },
					{ label: '股東權益', value: formatLargeNumber(a.financial_health.total_equity) },
					{ label: '總負債', value: formatLargeNumber(a.financial_health.total_debt) },
					{ label: '現金', value: formatLargeNumber(a.financial_health.total_cash) },
					{ label: '流動比率', value: formatDecimal(a.financial_health.current_ratio) },
					{ label: '速動比率', value: formatDecimal(a.financial_health.quick_ratio) },
					{ label: '營運資金', value: formatLargeNumber(a.financial_health.working_capital) },
				]} />

				<h3 class="text-base font-semibold text-[#e4e7ec]">營收 / 淨利 / EBITDA 趨勢</h3>
				<FinancialChart
					datasets={[
						{ label: '營收', data: a.financial_health.revenue_history, color: '#3b82f6' },
						{ label: '淨利', data: a.financial_health.net_income_history, color: '#22c55e' },
						{ label: 'EBITDA', data: a.financial_health.ebitda_history, color: '#f59e0b' },
					]}
				/>

				<h3 class="text-base font-semibold text-[#e4e7ec]">毛利率 / 營益率趨勢</h3>
				<FinancialChart
					datasets={[
						{ label: '毛利率', data: a.financial_health.gross_margin_history, color: '#3b82f6', type: 'line' },
						{ label: '營益率', data: a.financial_health.operating_margin_history, color: '#22c55e', type: 'line' },
					]}
					isPercentage
				/>

				<h3 class="text-base font-semibold text-[#e4e7ec]">現金流趨勢</h3>
				<FinancialChart
					datasets={[
						{ label: '營業現金流', data: a.financial_health.operating_cashflow_history, color: '#3b82f6' },
						{ label: '資本支出', data: a.financial_health.capex_history, color: '#ef4444' },
						{ label: '自由現金流', data: a.financial_health.free_cashflow_history, color: '#22c55e' },
					]}
				/>
			</div>

		<!-- T3: 成長動能 -->
		{:else if activeTab === 't3'}
			<div class="space-y-6">
				<h3 class="text-base font-semibold text-[#e4e7ec]">成長率</h3>
				<MetricsGrid metrics={[
					{ label: '營收成長', value: formatPercent(a.growth_momentum.revenue_growth, true), color: valueColor(a.growth_momentum.revenue_growth) },
					{ label: '盈餘成長', value: formatPercent(a.growth_momentum.earnings_growth, true), color: valueColor(a.growth_momentum.earnings_growth) },
					{ label: '季度盈餘成長', value: formatPercent(a.growth_momentum.earnings_quarterly_growth, true), color: valueColor(a.growth_momentum.earnings_quarterly_growth) },
				]} columns={3} />

				{#if a.growth_momentum.eps_estimates.length > 0}
					<h3 class="text-base font-semibold text-[#e4e7ec]">EPS 預估</h3>
					<div class="overflow-x-auto rounded-lg border border-[#2d3142]">
						<table class="w-full text-sm">
							<thead class="bg-[#252836] text-[#8b8fa3]">
								<tr>
									<th class="px-3 py-2.5 text-left font-medium">期間</th>
									<th class="px-3 py-2.5 text-left font-medium">均值</th>
									<th class="px-3 py-2.5 text-left font-medium">最低</th>
									<th class="px-3 py-2.5 text-left font-medium">最高</th>
									<th class="px-3 py-2.5 text-left font-medium">去年同期</th>
									<th class="px-3 py-2.5 text-left font-medium">成長率</th>
									<th class="px-3 py-2.5 text-left font-medium">分析師</th>
								</tr>
							</thead>
							<tbody>
								{#each a.growth_momentum.eps_estimates as est}
									<tr class="border-t border-[#2d3142] hover:bg-[#252836]">
										<td class="px-3 py-2.5 font-medium text-[#e4e7ec]">{est.period}</td>
										<td class="px-3 py-2.5">{formatDecimal(est.avg)}</td>
										<td class="px-3 py-2.5">{formatDecimal(est.low)}</td>
										<td class="px-3 py-2.5">{formatDecimal(est.high)}</td>
										<td class="px-3 py-2.5">{formatDecimal(est.yearAgoEps)}</td>
										<td class="px-3 py-2.5 {valueColor(est.growth)}">{formatPercent(est.growth, true)}</td>
										<td class="px-3 py-2.5">{est.numberOfAnalysts ?? '—'}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}

				{#if a.growth_momentum.revenue_estimates.length > 0}
					<h3 class="text-base font-semibold text-[#e4e7ec]">營收預估</h3>
					<div class="overflow-x-auto rounded-lg border border-[#2d3142]">
						<table class="w-full text-sm">
							<thead class="bg-[#252836] text-[#8b8fa3]">
								<tr>
									<th class="px-3 py-2.5 text-left font-medium">期間</th>
									<th class="px-3 py-2.5 text-left font-medium">均值</th>
									<th class="px-3 py-2.5 text-left font-medium">最低</th>
									<th class="px-3 py-2.5 text-left font-medium">最高</th>
									<th class="px-3 py-2.5 text-left font-medium">成長率</th>
									<th class="px-3 py-2.5 text-left font-medium">分析師</th>
								</tr>
							</thead>
							<tbody>
								{#each a.growth_momentum.revenue_estimates as est}
									<tr class="border-t border-[#2d3142] hover:bg-[#252836]">
										<td class="px-3 py-2.5 font-medium text-[#e4e7ec]">{est.period}</td>
										<td class="px-3 py-2.5">{formatLargeNumber(est.avg)}</td>
										<td class="px-3 py-2.5">{formatLargeNumber(est.low)}</td>
										<td class="px-3 py-2.5">{formatLargeNumber(est.high)}</td>
										<td class="px-3 py-2.5 {valueColor(est.growth)}">{formatPercent(est.growth, true)}</td>
										<td class="px-3 py-2.5">{est.numberOfAnalysts ?? '—'}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}

				<h3 class="text-base font-semibold text-[#e4e7ec]">盈餘驚喜</h3>
				{#if surpriseConfig}
					<ChartCanvas config={surpriseConfig} height="260px" />
				{:else}
					<p class="text-[#8b8fa3] text-sm">無盈餘驚喜資料</p>
				{/if}
			</div>

		<!-- T4: 風險分析 -->
		{:else if activeTab === 't4'}
			<div class="space-y-6">
				<h3 class="text-base font-semibold text-[#e4e7ec]">風險指標</h3>
				<MetricsGrid metrics={[
					{ label: 'Beta', value: formatDecimal(a.risk_metrics.beta) },
					{ label: '放空比率', value: formatDecimal(a.risk_metrics.short_ratio) },
					{ label: '放空佔流通股%', value: formatPercentPlain(a.risk_metrics.short_percent_of_float, true) },
					{ label: '52 週高點', value: formatCurrency(a.risk_metrics.fifty_two_week_high) },
					{ label: '52 週低點', value: formatCurrency(a.risk_metrics.fifty_two_week_low) },
					{ label: '52 週漲跌', value: formatPercent(a.risk_metrics.fifty_two_week_change, true), color: valueColor(a.risk_metrics.fifty_two_week_change) },
					{ label: '機構持股', value: formatPercentPlain(a.risk_metrics.held_percent_institutions, true) },
					{ label: '內部持股', value: formatPercentPlain(a.risk_metrics.held_percent_insiders, true) },
				]} />

				<!-- 52 週價格範圍視覺化 -->
				{#if a.risk_metrics.fifty_two_week_low && a.risk_metrics.fifty_two_week_high && a.current_price}
					{@const low = a.risk_metrics.fifty_two_week_low}
					{@const high = a.risk_metrics.fifty_two_week_high}
					{@const price = a.current_price}
					{@const pct = ((price - low) / (high - low)) * 100}
					<div class="bg-[#252836] rounded-lg p-4">
						<div class="text-sm text-[#8b8fa3] mb-2">52 週價格區間</div>
						<div class="flex items-center gap-3 text-sm">
							<span class="text-[#ef4444]">{formatCurrency(low)}</span>
							<div class="flex-1 relative h-3 bg-[#2d3142] rounded-full overflow-hidden">
								<div class="absolute left-0 top-0 h-full bg-gradient-to-r from-[#ef4444] to-[#22c55e] rounded-full" style="width: 100%;"></div>
								<div
									class="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-[#3b82f6] rounded-full border-2 border-[#e4e7ec] shadow"
									style="left: {pct}%; transform: translate(-50%, -50%);"
								></div>
							</div>
							<span class="text-[#22c55e]">{formatCurrency(high)}</span>
						</div>
						<div class="text-center text-xs text-[#8b8fa3] mt-1">
							現價 {formatCurrency(price)}（區間 {pct.toFixed(0)}%）
						</div>
					</div>
				{/if}

				{#if a.risk_metrics.insider_transactions.length > 0}
					<h3 class="text-base font-semibold text-[#e4e7ec]">近期內部交易</h3>
					<div class="overflow-x-auto rounded-lg border border-[#2d3142]">
						<table class="w-full text-sm">
							<thead class="bg-[#252836] text-[#8b8fa3]">
								<tr>
									<th class="px-3 py-2.5 text-left font-medium">日期</th>
									<th class="px-3 py-2.5 text-left font-medium">內部人</th>
									<th class="px-3 py-2.5 text-left font-medium">職位</th>
									<th class="px-3 py-2.5 text-left font-medium">類型</th>
									<th class="px-3 py-2.5 text-left font-medium">股數</th>
									<th class="px-3 py-2.5 text-left font-medium">金額</th>
								</tr>
							</thead>
							<tbody>
								{#each a.risk_metrics.insider_transactions.slice(0, 10) as tx}
									<tr class="border-t border-[#2d3142] hover:bg-[#252836]">
										<td class="px-3 py-2.5 text-[#e4e7ec]">{tx.date?.substring(0, 10) ?? '—'}</td>
										<td class="px-3 py-2.5">{tx.insider ?? '—'}</td>
										<td class="px-3 py-2.5 text-[#8b8fa3]">{tx.position ?? '—'}</td>
										<td class="px-3 py-2.5">
											<span class="{tx.transaction?.toLowerCase().includes('buy') || tx.transaction?.toLowerCase().includes('purchase') ? 'text-[#22c55e]' : 'text-[#ef4444]'}">
												{tx.transaction ?? '—'}
											</span>
										</td>
										<td class="px-3 py-2.5">{formatNumber(tx.shares ?? 0)}</td>
										<td class="px-3 py-2.5">{formatLargeNumber(tx.value)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}

				{#if a.risk_metrics.top_institutional_holders.length > 0}
					<h3 class="text-base font-semibold text-[#e4e7ec]">主要機構持股人</h3>
					<div class="overflow-x-auto rounded-lg border border-[#2d3142]">
						<table class="w-full text-sm">
							<thead class="bg-[#252836] text-[#8b8fa3]">
								<tr>
									<th class="px-3 py-2.5 text-left font-medium">機構</th>
									<th class="px-3 py-2.5 text-left font-medium">持股比例</th>
									<th class="px-3 py-2.5 text-left font-medium">持股數</th>
									<th class="px-3 py-2.5 text-left font-medium">市值</th>
								</tr>
							</thead>
							<tbody>
								{#each a.risk_metrics.top_institutional_holders as holder}
									<tr class="border-t border-[#2d3142] hover:bg-[#252836]">
										<td class="px-3 py-2.5 text-[#e4e7ec]">{holder.holder}</td>
										<td class="px-3 py-2.5">{formatPercentPlain(holder.pct_held, true)}</td>
										<td class="px-3 py-2.5">{formatNumber(holder.shares ?? 0)}</td>
										<td class="px-3 py-2.5">{formatLargeNumber(holder.value)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</div>

		<!-- T5: 同業比較 -->
		{:else if activeTab === 't5'}
			<div class="space-y-6">
				<div class="text-sm text-[#8b8fa3]">
					產業：{a.peer_comparison.sector} · {a.peer_comparison.industry}
				</div>

				<div class="grid grid-cols-2 gap-6">
					<div>
						<h3 class="text-base font-semibold text-[#e4e7ec] mb-4">能力雷達圖</h3>
						<PeerRadar comparison={a.peer_comparison} targetSymbol={a.symbol} />
					</div>
					<div>
						<h3 class="text-base font-semibold text-[#e4e7ec] mb-4">同業排名表</h3>
						<PeerTable comparison={a.peer_comparison} targetSymbol={a.symbol} />
					</div>
				</div>
			</div>
		{/if}
	</AnalysisTabs>
</div>
