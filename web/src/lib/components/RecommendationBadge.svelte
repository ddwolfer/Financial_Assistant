<script lang="ts">
	/**
	 * 分析師推薦徽章。
	 */
	let { recommendation, mean }: { recommendation: string | null; mean: number | null } = $props();

	const config: Record<string, { bg: string; text: string; label: string }> = {
		'strong_buy': { bg: 'bg-[#22c55e]/20', text: 'text-[#22c55e]', label: '強力買入' },
		'buy': { bg: 'bg-[#22c55e]/15', text: 'text-[#22c55e]', label: '買入' },
		'hold': { bg: 'bg-[#f59e0b]/15', text: 'text-[#f59e0b]', label: '持有' },
		'sell': { bg: 'bg-[#ef4444]/15', text: 'text-[#ef4444]', label: '賣出' },
		'strong_sell': { bg: 'bg-[#ef4444]/20', text: 'text-[#ef4444]', label: '強力賣出' },
	};

	const style = $derived(config[recommendation ?? ''] ?? config['hold']);
</script>

{#if recommendation}
	<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium {style.bg} {style.text}">
		{style.label}
		{#if mean != null}
			<span class="text-xs opacity-75">({mean.toFixed(1)})</span>
		{/if}
	</span>
{:else}
	<span class="text-[#8b8fa3] text-sm">—</span>
{/if}
