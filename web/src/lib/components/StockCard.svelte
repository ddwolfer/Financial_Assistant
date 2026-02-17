<script lang="ts">
	/**
	 * 股票卡片 — 顯示在首頁通過名單中。
	 */
	import type { ScreeningResult } from '$lib/types';
	import { formatDecimal, formatPercent, formatCurrency, valueColor } from '$lib/utils';

	let { stock }: { stock: ScreeningResult } = $props();
</script>

<a
	href="/stock/{stock.symbol}"
	class="block bg-[#1a1d29] border border-[#2d3142] rounded-lg p-4 hover:bg-[#252836] hover:border-[#3b82f6]/50 transition-all no-underline"
>
	<div class="flex items-center justify-between mb-2">
		<div>
			<span class="text-[#e4e7ec] font-bold text-sm">{stock.symbol}</span>
			<span class="text-[#8b8fa3] text-xs ml-2">{stock.metrics.company_name ?? ''}</span>
		</div>
		<span class="text-xs px-2 py-0.5 rounded bg-[#22c55e]/15 text-[#22c55e] font-medium">
			通過
		</span>
	</div>

	<div class="grid grid-cols-4 gap-3 text-xs">
		<div>
			<div class="text-[#8b8fa3]">現價</div>
			<div class="text-[#e4e7ec] font-medium">{formatCurrency(stock.current_price)}</div>
		</div>
		<div>
			<div class="text-[#8b8fa3]">葛拉漢數</div>
			<div class="text-[#e4e7ec] font-medium">{formatCurrency(stock.graham_number)}</div>
		</div>
		<div>
			<div class="text-[#8b8fa3]">安全邊際</div>
			<div class="{valueColor(stock.margin_of_safety_pct)} font-medium">
				{formatPercent(stock.margin_of_safety_pct)}
			</div>
		</div>
		<div>
			<div class="text-[#8b8fa3]">本益比 P/E</div>
			<div class="text-[#e4e7ec] font-medium">{formatDecimal(stock.metrics.trailing_pe)}</div>
		</div>
	</div>
</a>
