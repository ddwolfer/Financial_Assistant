<script lang="ts">
	/**
	 * 指標網格 — 用於顯示鍵值對指標。
	 */
	interface Metric {
		label: string;
		value: string;
		color?: string;
	}

	let { metrics, columns = 4 }: { metrics: Metric[]; columns?: number } = $props();
</script>

<div class="grid gap-4" style="grid-template-columns: repeat({columns}, minmax(0, 1fr));">
	{#each metrics as m}
		<div class="bg-[#252836] rounded-lg p-3">
			<div class="text-[#8b8fa3] text-xs mb-1">{m.label}</div>
			<div class="font-semibold text-sm {m.color ?? 'text-[#e4e7ec]'}">{m.value}</div>
		</div>
	{/each}
</div>
