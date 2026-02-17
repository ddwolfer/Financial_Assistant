<script lang="ts">
	/**
	 * 同業比較表。
	 */
	import type { PeerMetrics, PeerComparisonData } from '$lib/types';
	import { formatDecimal, formatPercentPlain, formatLargeNumber } from '$lib/utils';

	let { comparison, targetSymbol }: { comparison: PeerComparisonData; targetSymbol: string } = $props();

	const columns = [
		{ key: 'symbol', label: '代碼' },
		{ key: 'pe', label: 'P/E', fmt: (v: number | null) => formatDecimal(v) },
		{ key: 'forward_pe', label: 'Fwd P/E', fmt: (v: number | null) => formatDecimal(v) },
		{ key: 'ev_ebitda', label: 'EV/EBITDA', fmt: (v: number | null) => formatDecimal(v) },
		{ key: 'roe', label: 'ROE', fmt: (v: number | null) => formatPercentPlain(v, true) },
		{ key: 'gross_margin', label: '毛利率', fmt: (v: number | null) => formatPercentPlain(v, true) },
		{ key: 'operating_margin', label: '營益率', fmt: (v: number | null) => formatPercentPlain(v, true) },
		{ key: 'revenue_growth', label: '營收成長', fmt: (v: number | null) => formatPercentPlain(v, true) },
		{ key: 'market_cap', label: '市值', fmt: (v: number | null) => formatLargeNumber(v) },
		{ key: 'debt_to_equity', label: 'D/E', fmt: (v: number | null) => formatDecimal(v) },
	];
</script>

<div class="overflow-x-auto rounded-lg border border-[#2d3142]">
	<table class="w-full text-sm">
		<thead class="bg-[#252836] text-[#8b8fa3]">
			<tr>
				{#each columns as col}
					<th class="px-3 py-2.5 text-left font-medium whitespace-nowrap">{col.label}</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each comparison.peers as peer (peer.symbol)}
				<tr class="border-t border-[#2d3142] {peer.symbol === targetSymbol ? 'bg-[#3b82f6]/10' : 'hover:bg-[#252836]'}">
					<td class="px-3 py-2.5 font-bold {peer.symbol === targetSymbol ? 'text-[#3b82f6]' : 'text-[#e4e7ec]'}">
						{peer.symbol}
						{#if peer.symbol === targetSymbol}
							<span class="text-xs text-[#3b82f6] ml-1">★</span>
						{/if}
					</td>
					{#each columns.slice(1) as col}
						<td class="px-3 py-2.5 text-[#e4e7ec]">
							{col.fmt((peer as any)[col.key])}
						</td>
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>
</div>

{#if comparison.rank_in_peers && Object.keys(comparison.rank_in_peers).length > 0}
	<div class="mt-4">
		<h4 class="text-sm font-medium text-[#e4e7ec] mb-2">排名</h4>
		<div class="flex flex-wrap gap-3">
			{#each Object.entries(comparison.rank_in_peers) as [metric, rank]}
				<div class="bg-[#252836] rounded px-3 py-1.5 text-xs">
					<span class="text-[#8b8fa3]">{metric}:</span>
					<span class="text-[#f59e0b] font-bold ml-1">#{rank}</span>
					<span class="text-[#8b8fa3]">/ {comparison.peers.length}</span>
				</div>
			{/each}
		</div>
	</div>
{/if}
