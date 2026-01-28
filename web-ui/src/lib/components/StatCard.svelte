<script lang="ts">
	interface Props {
		title: string;
		count: number;
		href: string;
		suffix?: string;
		icon?: string;
	}

	let { title, count, href, suffix, icon }: Props = $props();
</script>

<div class="bg-white rounded-lg shadow p-6">
	<div class="flex items-center justify-between mb-4">
		<h3 class="text-lg font-semibold text-gray-700">{title}</h3>
		{#if icon}
			<span class="text-3xl">{icon}</span>
		{/if}
	</div>
	<p class="text-3xl font-bold text-gray-900 mb-4">
		{count}{#if suffix}<span class="text-lg font-normal text-gray-600 ml-2">{suffix}</span>{/if}
	</p>
	<a
		{href}
		class="inline-block text-blue-600 hover:text-blue-800 font-medium transition-colors"
	>
		View All →
	</a>
</div>
