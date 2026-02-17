<script lang="ts">
	import '../app.css';
	import { page } from '$app/state';

	let { children } = $props();

	const navItems = [
		{ href: '/', label: '總覽' },
		{ href: '/screening', label: '篩選結果' },
	];
</script>

<div class="min-h-screen flex flex-col">
	<!-- 頂部導覽列 -->
	<nav class="bg-[#1a1d29] border-b border-[#2d3142] px-6 py-3 flex items-center gap-8">
		<a href="/" class="flex items-center gap-2 text-lg font-bold text-[#e4e7ec] no-underline">
			<span class="text-xl">📊</span>
			<span>量化分析儀表板</span>
		</a>

		<div class="flex gap-1">
			{#each navItems as item}
				<a
					href={item.href}
					class="px-4 py-2 rounded-lg text-sm font-medium transition-colors no-underline
						{page.url.pathname === item.href
							? 'bg-[#3b82f6] text-white'
							: 'text-[#8b8fa3] hover:text-[#e4e7ec] hover:bg-[#252836]'}"
				>
					{item.label}
				</a>
			{/each}
		</div>

		<div class="ml-auto text-xs text-[#8b8fa3]">
			Quant-Analyst-Agent
		</div>
	</nav>

	<!-- 主內容區 -->
	<main class="flex-1 p-6 max-w-7xl mx-auto w-full">
		{@render children()}
	</main>
</div>
