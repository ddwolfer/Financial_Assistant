<script lang="ts">
	/**
	 * 產業分布圓餅圖。
	 */
	import ChartCanvas from './ChartCanvas.svelte';
	import type { ScreeningResult } from '$lib/types';

	let { results }: { results: ScreeningResult[] } = $props();

	// 計算各產業通過的股票數
	const sectorCounts = $derived.by(() => {
		const counts: Record<string, number> = {};
		for (const r of results) {
			if (r.passed && r.metrics.sector) {
				counts[r.metrics.sector] = (counts[r.metrics.sector] || 0) + 1;
			}
		}
		return Object.entries(counts)
			.sort((a, b) => b[1] - a[1]);
	});

	const COLORS = [
		'#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6',
		'#ec4899', '#06b6d4', '#f97316', '#14b8a6', '#6366f1',
		'#84cc16', '#e11d48',
	];

	const chartConfig = $derived({
		type: 'doughnut' as const,
		data: {
			labels: sectorCounts.map(([s]) => s),
			datasets: [{
				data: sectorCounts.map(([, c]) => c),
				backgroundColor: COLORS.slice(0, sectorCounts.length),
				borderColor: '#1a1d29',
				borderWidth: 2,
			}],
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				legend: {
					position: 'right' as const,
					labels: {
						color: '#e4e7ec',
						padding: 12,
						font: { size: 12 },
					},
				},
			},
		},
	});
</script>

{#if sectorCounts.length > 0}
	<ChartCanvas config={chartConfig} height="280px" />
{:else}
	<p class="text-[#8b8fa3] text-sm text-center py-8">無通過篩選的股票</p>
{/if}
