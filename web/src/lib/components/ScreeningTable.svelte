<script lang="ts">
	/**
	 * 篩選結果資料表 — 可排序、搜尋、篩選。
	 */
	import type { ScreeningResult } from '$lib/types';
	import { formatDecimal, formatPercent, formatCurrency, valueColor } from '$lib/utils';

	let { results }: { results: ScreeningResult[] } = $props();

	// 篩選與排序狀態
	let search = $state('');
	let sectorFilter = $state('all');
	let showOnlyPassed = $state(false);
	let sortKey = $state<string>('margin_of_safety_pct');
	let sortAsc = $state(false);

	// 取得所有產業（去重排序）
	const sectors = $derived(
		[...new Set(results.map((r) => r.metrics.sector).filter(Boolean))].sort() as string[]
	);

	// 篩選後的結果
	const filtered = $derived.by(() => {
		let list = results;

		if (showOnlyPassed) {
			list = list.filter((r) => r.passed);
		}

		if (sectorFilter !== 'all') {
			list = list.filter((r) => r.metrics.sector === sectorFilter);
		}

		if (search.trim()) {
			const q = search.trim().toLowerCase();
			list = list.filter(
				(r) =>
					r.symbol.toLowerCase().includes(q) ||
					(r.metrics.company_name?.toLowerCase().includes(q) ?? false)
			);
		}

		// 排序
		list = [...list].sort((a, b) => {
			const va = getSortValue(a, sortKey);
			const vb = getSortValue(b, sortKey);
			if (va == null && vb == null) return 0;
			if (va == null) return 1;
			if (vb == null) return -1;
			const diff = va < vb ? -1 : va > vb ? 1 : 0;
			return sortAsc ? diff : -diff;
		});

		return list;
	});

	function getSortValue(r: ScreeningResult, key: string): number | string | null {
		switch (key) {
			case 'symbol': return r.symbol;
			case 'company_name': return r.metrics.company_name;
			case 'sector': return r.metrics.sector;
			case 'trailing_pe': return r.metrics.trailing_pe;
			case 'peg_ratio': return r.metrics.peg_ratio;
			case 'roe': return r.metrics.roe;
			case 'debt_to_equity': return r.metrics.debt_to_equity;
			case 'graham_number': return r.graham_number;
			case 'current_price': return r.current_price;
			case 'margin_of_safety_pct': return r.margin_of_safety_pct;
			case 'passed': return r.passed ? 1 : 0;
			default: return null;
		}
	}

	function toggleSort(key: string) {
		if (sortKey === key) {
			sortAsc = !sortAsc;
		} else {
			sortKey = key;
			sortAsc = false;
		}
	}

	function sortIndicator(key: string): string {
		if (sortKey !== key) return '';
		return sortAsc ? ' ↑' : ' ↓';
	}

	const columns = [
		{ key: 'symbol', label: '代碼' },
		{ key: 'company_name', label: '公司名稱' },
		{ key: 'sector', label: '產業' },
		{ key: 'trailing_pe', label: 'P/E' },
		{ key: 'peg_ratio', label: 'PEG' },
		{ key: 'roe', label: 'ROE' },
		{ key: 'debt_to_equity', label: 'D/E' },
		{ key: 'graham_number', label: '葛拉漢數' },
		{ key: 'current_price', label: '現價' },
		{ key: 'margin_of_safety_pct', label: '安全邊際' },
		{ key: 'passed', label: '結果' },
	] as const;
</script>

<div class="space-y-4">
	<!-- 篩選工具列 -->
	<div class="flex items-center gap-4 flex-wrap">
		<input
			type="text"
			placeholder="搜尋代碼或公司名稱..."
			bind:value={search}
			class="bg-[#252836] border border-[#2d3142] rounded-lg px-3 py-2 text-sm text-[#e4e7ec] placeholder-[#8b8fa3] outline-none focus:border-[#3b82f6] w-64"
		/>

		<select
			bind:value={sectorFilter}
			class="bg-[#252836] border border-[#2d3142] rounded-lg px-3 py-2 text-sm text-[#e4e7ec] outline-none focus:border-[#3b82f6]"
		>
			<option value="all">全部產業</option>
			{#each sectors as sector}
				<option value={sector}>{sector}</option>
			{/each}
		</select>

		<label class="flex items-center gap-2 text-sm text-[#8b8fa3] cursor-pointer">
			<input
				type="checkbox"
				bind:checked={showOnlyPassed}
				class="accent-[#3b82f6]"
			/>
			僅顯示通過
		</label>

		<span class="ml-auto text-xs text-[#8b8fa3]">
			顯示 {filtered.length} / {results.length} 筆
		</span>
	</div>

	<!-- 資料表 -->
	<div class="overflow-x-auto rounded-lg border border-[#2d3142]">
		<table class="w-full text-sm">
			<thead class="bg-[#252836] text-[#8b8fa3]">
				<tr>
					{#each columns as col}
						<th
							class="px-3 py-2.5 text-left font-medium cursor-pointer hover:text-[#e4e7ec] transition-colors whitespace-nowrap select-none"
							onclick={() => toggleSort(col.key)}
						>
							{col.label}{sortIndicator(col.key)}
						</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each filtered as row (row.symbol)}
					<tr
						class="border-t border-[#2d3142] hover:bg-[#252836] cursor-pointer transition-colors"
						onclick={() => window.location.href = `/stock/${row.symbol}`}
					>
						<td class="px-3 py-2.5 font-bold text-[#3b82f6]">{row.symbol}</td>
						<td class="px-3 py-2.5 text-[#e4e7ec] max-w-[180px] truncate">{row.metrics.company_name ?? '—'}</td>
						<td class="px-3 py-2.5 text-[#8b8fa3]">{row.metrics.sector ?? '—'}</td>
						<td class="px-3 py-2.5">{formatDecimal(row.metrics.trailing_pe)}</td>
						<td class="px-3 py-2.5">{formatDecimal(row.metrics.peg_ratio)}</td>
						<td class="px-3 py-2.5">{formatPercent(row.metrics.roe, true)}</td>
						<td class="px-3 py-2.5">{formatDecimal(row.metrics.debt_to_equity)}</td>
						<td class="px-3 py-2.5">{formatCurrency(row.graham_number)}</td>
						<td class="px-3 py-2.5">{formatCurrency(row.current_price)}</td>
						<td class="px-3 py-2.5 {valueColor(row.margin_of_safety_pct)} font-medium">
							{formatPercent(row.margin_of_safety_pct)}
						</td>
						<td class="px-3 py-2.5">
							{#if row.passed}
								<span class="px-2 py-0.5 rounded text-xs font-medium bg-[#22c55e]/15 text-[#22c55e]">通過</span>
							{:else}
								<span class="px-2 py-0.5 rounded text-xs font-medium bg-[#ef4444]/15 text-[#ef4444]">未通過</span>
							{/if}
						</td>
					</tr>
				{/each}

				{#if filtered.length === 0}
					<tr>
						<td colspan={columns.length} class="px-3 py-8 text-center text-[#8b8fa3]">
							無符合條件的結果
						</td>
					</tr>
				{/if}
			</tbody>
		</table>
	</div>
</div>
