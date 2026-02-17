<script lang="ts">
	/**
	 * Chart.js 通用 canvas 元件。
	 * 接收 Chart.js 設定，自動建立與銷毀圖表。
	 */
	import { onMount } from 'svelte';
	import { Chart, registerables } from 'chart.js';

	Chart.register(...registerables);

	// Chart.js 全域深色主題設定
	Chart.defaults.color = '#8b8fa3';
	Chart.defaults.borderColor = '#2d3142';

	let { config, height = '300px' }: { config: any; height?: string } = $props();

	let canvasEl: HTMLCanvasElement;
	let chart: Chart | null = null;

	onMount(() => {
		chart = new Chart(canvasEl, config);
		return () => {
			chart?.destroy();
		};
	});

	$effect(() => {
		if (chart && config) {
			chart.data = config.data;
			if (config.options) {
				chart.options = config.options;
			}
			chart.update();
		}
	});
</script>

<div style="height: {height}; position: relative;">
	<canvas bind:this={canvasEl}></canvas>
</div>
