<script lang="ts">
	import SectorChart from '$lib/components/SectorChart.svelte';
	import StockCard from '$lib/components/StockCard.svelte';
	import { formatNumber } from '$lib/utils';

	let { data } = $props();

	const passRate = $derived(
		data.screening.total_screened > 0
			? ((data.screening.total_passed / data.screening.total_screened) * 100).toFixed(1)
			: '0'
	);

	const passedStocks = $derived(
		data.screening.results
			.filter((r) => r.passed)
			.sort((a, b) => (b.margin_of_safety_pct ?? -999) - (a.margin_of_safety_pct ?? -999))
	);

	const timestamp = $derived(
		new Date(data.screening.timestamp).toLocaleString('zh-TW', {
			year: 'numeric', month: '2-digit', day: '2-digit',
			hour: '2-digit', minute: '2-digit',
		})
	);
</script>

<div class="space-y-6">
	<!-- 標題區 -->
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold text-[#e4e7ec]">篩選總覽</h1>
		<div class="text-xs text-[#8b8fa3]">
			最後更新：{timestamp}
		</div>
	</div>

	<!-- 大數字卡片 -->
	<div class="grid grid-cols-4 gap-4">
		<div class="bg-[#1a1d29] border border-[#2d3142] rounded-lg p-5">
			<div class="text-[#8b8fa3] text-sm mb-1">總篩選數</div>
			<div class="text-3xl font-bold text-[#e4e7ec]">{formatNumber(data.screening.total_screened)}</div>
		</div>
		<div class="bg-[#1a1d29] border border-[#2d3142] rounded-lg p-5">
			<div class="text-[#8b8fa3] text-sm mb-1">通過篩選</div>
			<div class="text-3xl font-bold text-[#22c55e]">{formatNumber(data.screening.total_passed)}</div>
		</div>
		<div class="bg-[#1a1d29] border border-[#2d3142] rounded-lg p-5">
			<div class="text-[#8b8fa3] text-sm mb-1">通過率</div>
			<div class="text-3xl font-bold text-[#f59e0b]">{passRate}%</div>
		</div>
		<div class="bg-[#1a1d29] border border-[#2d3142] rounded-lg p-5">
			<div class="text-[#8b8fa3] text-sm mb-1">已深度分析</div>
			<div class="text-3xl font-bold text-[#3b82f6]">{data.symbols.count}</div>
		</div>
	</div>

	<!-- 產業分布 + 通過名單 -->
	<div class="grid grid-cols-3 gap-6">
		<!-- 產業分布圖 -->
		<div class="bg-[#1a1d29] border border-[#2d3142] rounded-lg p-5">
			<h2 class="text-base font-semibold text-[#e4e7ec] mb-4">通過股票產業分布</h2>
			<SectorChart results={data.screening.results} />
		</div>

		<!-- 通過股票名單 -->
		<div class="col-span-2 bg-[#1a1d29] border border-[#2d3142] rounded-lg p-5">
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-base font-semibold text-[#e4e7ec]">
					通過篩選的股票（依安全邊際排序）
				</h2>
				<a href="/screening" class="text-sm text-[#3b82f6] hover:underline">
					查看全部 →
				</a>
			</div>

			<div class="space-y-2 max-h-[500px] overflow-y-auto pr-2">
				{#each passedStocks as stock (stock.symbol)}
					<StockCard {stock} />
				{/each}

				{#if passedStocks.length === 0}
					<p class="text-[#8b8fa3] text-sm text-center py-8">無通過篩選的股票</p>
				{/if}
			</div>
		</div>
	</div>

	<!-- 已分析股票快速連結 -->
	{#if data.symbols.symbols.length > 0}
		<div class="bg-[#1a1d29] border border-[#2d3142] rounded-lg p-5">
			<h2 class="text-base font-semibold text-[#e4e7ec] mb-3">已完成深度分析</h2>
			<div class="flex flex-wrap gap-2">
				{#each data.symbols.symbols as sym}
					<a
						href="/stock/{sym}"
						class="px-3 py-1.5 bg-[#252836] border border-[#2d3142] rounded text-sm text-[#3b82f6] hover:bg-[#3b82f6]/15 hover:border-[#3b82f6]/50 transition-colors no-underline font-medium"
					>
						{sym}
					</a>
				{/each}
			</div>
		</div>
	{/if}
</div>
