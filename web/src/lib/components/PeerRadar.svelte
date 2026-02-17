<script lang="ts">
	/**
	 * 同業比較雷達圖。
	 */
	import ChartCanvas from './ChartCanvas.svelte';
	import type { PeerComparisonData } from '$lib/types';

	let { comparison, targetSymbol }: { comparison: PeerComparisonData; targetSymbol: string } = $props();

	// 用於雷達圖的指標（數值正規化到 0-100）
	const radarMetrics = ['roe', 'gross_margin', 'operating_margin', 'revenue_growth', 'earnings_growth'] as const;
	const radarLabels = ['ROE', '毛利率', '營益率', '營收成長', '盈餘成長'];

	const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

	// 正規化：取各指標在同業中的百分位排名，轉為 0-100
	function normalize(peers: any[], metric: string): number[] {
		const values = peers.map((p) => p[metric] ?? 0);
		const min = Math.min(...values);
		const max = Math.max(...values);
		const range = max - min || 1;
		return values.map((v) => ((v - min) / range) * 100);
	}

	const chartConfig = $derived.by(() => {
		const peers = comparison.peers;
		if (peers.length === 0) return null;

		const normalized: Record<string, number[]> = {};
		for (const m of radarMetrics) {
			normalized[m] = normalize(peers, m);
		}

		// 只取前 5 個同業（含目標）
		const displayPeers = peers.slice(0, 5);

		return {
			type: 'radar' as const,
			data: {
				labels: radarLabels,
				datasets: displayPeers.map((peer, i) => ({
					label: peer.symbol,
					data: radarMetrics.map((m) => normalized[m][peers.indexOf(peer)]),
					borderColor: peer.symbol === targetSymbol ? '#3b82f6' : COLORS[i % COLORS.length],
					backgroundColor: peer.symbol === targetSymbol ? '#3b82f620' : 'transparent',
					borderWidth: peer.symbol === targetSymbol ? 3 : 1.5,
					pointRadius: 3,
					pointBackgroundColor: peer.symbol === targetSymbol ? '#3b82f6' : COLORS[i % COLORS.length],
				})),
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						position: 'bottom' as const,
						labels: { color: '#e4e7ec', font: { size: 11 }, padding: 15 },
					},
				},
				scales: {
					r: {
						ticks: { color: '#8b8fa3', backdropColor: 'transparent', font: { size: 10 } },
						grid: { color: '#2d3142' },
						pointLabels: { color: '#e4e7ec', font: { size: 11 } },
						suggestedMin: 0,
						suggestedMax: 100,
					},
				},
			},
		};
	});
</script>

{#if chartConfig}
	<ChartCanvas config={chartConfig} height="350px" />
{:else}
	<p class="text-[#8b8fa3] text-sm text-center py-6">無同業比較資料</p>
{/if}
