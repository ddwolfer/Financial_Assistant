<script lang="ts">
	import ScreeningTable from '$lib/components/ScreeningTable.svelte';
	import { formatNumber } from '$lib/utils';

	let { data } = $props();

	const timestamp = $derived(
		new Date(data.screening.timestamp).toLocaleString('zh-TW', {
			year: 'numeric', month: '2-digit', day: '2-digit',
			hour: '2-digit', minute: '2-digit',
		})
	);
</script>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-[#e4e7ec]">篩選結果</h1>
			<p class="text-sm text-[#8b8fa3] mt-1">
				模式：{data.screening.screening_mode === 'dual_track' ? '雙軌制' : '絕對門檻'} ·
				{formatNumber(data.screening.total_screened)} 標的 ·
				{formatNumber(data.screening.total_passed)} 通過 ·
				{timestamp}
			</p>
		</div>
	</div>

	<ScreeningTable results={data.screening.results} />
</div>
