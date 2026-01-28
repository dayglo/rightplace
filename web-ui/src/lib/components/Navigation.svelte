<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { checkHealth } from '$lib/services/api';

	let serverStatus: 'checking' | 'healthy' | 'unhealthy' = $state('checking');
	let intervalId: number | undefined;

	async function checkServerHealth() {
		try {
			await checkHealth();
			serverStatus = 'healthy';
		} catch (error) {
			serverStatus = 'unhealthy';
		}
	}

	onMount(() => {
		// Check immediately
		checkServerHealth();

		// Check every 30 seconds
		intervalId = window.setInterval(checkServerHealth, 30000);
	});

	onDestroy(() => {
		if (intervalId) {
			clearInterval(intervalId);
		}
	});

	function getStatusColor(status: typeof serverStatus): string {
		switch (status) {
			case 'healthy':
				return 'bg-green-500';
			case 'unhealthy':
				return 'bg-red-500';
			case 'checking':
				return 'bg-yellow-500';
		}
	}
</script>

<nav class="bg-white shadow">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
		<div class="flex justify-between h-16">
			<div class="flex items-center">
				<h1 class="text-2xl font-bold text-gray-900">Prison Roll Call</h1>
			</div>
			<div class="flex items-center">
				<span class="flex items-center text-sm text-gray-600">
					Server:
					<span
						data-testid="server-status"
						class="ml-2 h-3 w-3 rounded-full {getStatusColor(serverStatus)}"
					></span>
				</span>
			</div>
		</div>
	</div>
</nav>
