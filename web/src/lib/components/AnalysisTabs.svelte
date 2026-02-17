<script lang="ts">
	/**
	 * 分析分頁容器 — T1-T6 分頁導覽。
	 */
	import type { Snippet } from 'svelte';

	interface Tab {
		id: string;
		label: string;
	}

	let { tabs, activeTab = $bindable('t6'), children }: {
		tabs: Tab[];
		activeTab: string;
		children: Snippet;
	} = $props();
</script>

<div>
	<!-- 分頁標籤 -->
	<div class="flex border-b border-[#2d3142] mb-6 overflow-x-auto">
		{#each tabs as tab}
			<button
				class="px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors border-b-2
					{activeTab === tab.id
						? 'text-[#3b82f6] border-[#3b82f6]'
						: 'text-[#8b8fa3] border-transparent hover:text-[#e4e7ec] hover:border-[#8b8fa3]'}"
				onclick={() => (activeTab = tab.id)}
			>
				{tab.label}
			</button>
		{/each}
	</div>

	<!-- 分頁內容 -->
	{@render children()}
</div>
