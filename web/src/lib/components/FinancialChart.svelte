<script lang="ts">
	/**
	 * 通用財務趨勢圖 — 支援 bar 和 line 模式。
	 */
	import ChartCanvas from './ChartCanvas.svelte';
	import { sortedYears, formatLargeNumber } from '$lib/utils';

	interface Dataset {
		label: string;
		data: Record<string, number>;
		color: string;
		type?: 'bar' | 'line';
	}

	let { datasets, title = '', height = '260px', isPercentage = false }: {
		datasets: Dataset[];
		title?: string;
		height?: string;
		isPercentage?: boolean;
	} = $props();

	// 取得所有年份的聯集
	const years = $derived(
		[...new Set(datasets.flatMap((d) => sortedYears(d.data)))].sort()
	);

	const chartConfig = $derived({
		type: 'bar' as const,
		data: {
			labels: years,
			datasets: datasets.map((d) => ({
				label: d.label,
				data: years.map((y) => d.data[y] ?? null),
				backgroundColor: d.type === 'line' ? 'transparent' : d.color + '80',
				borderColor: d.color,
				borderWidth: d.type === 'line' ? 2 : 1,
				type: d.type || 'bar',
				tension: 0.3,
				pointRadius: d.type === 'line' ? 4 : 0,
				pointBackgroundColor: d.color,
			})),
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				legend: {
					labels: { color: '#e4e7ec', font: { size: 11 } },
				},
				title: title ? {
					display: true,
					text: title,
					color: '#e4e7ec',
					font: { size: 13, weight: 'bold' as const },
				} : { display: false },
			},
			scales: {
				x: {
					ticks: { color: '#8b8fa3' },
					grid: { color: '#2d3142' },
				},
				y: {
					ticks: {
						color: '#8b8fa3',
						callback: (value: number) =>
							isPercentage ? `${(value * 100).toFixed(0)}%` : formatLargeNumber(value),
					},
					grid: { color: '#2d3142' },
				},
			},
		},
	});
</script>

{#if years.length > 0}
	<ChartCanvas config={chartConfig} {height} />
{:else}
	<p class="text-[#8b8fa3] text-sm text-center py-6">無歷史資料</p>
{/if}
