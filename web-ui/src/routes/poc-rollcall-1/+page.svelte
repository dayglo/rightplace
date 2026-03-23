<script lang="ts">
	// POC Landing Page - Redirect to roll call list
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	onMount(() => {
		goto('/poc-rollcall-1/rollcalls');
	});
</script>

<div class="min-h-screen bg-gray-50 flex items-center justify-center">
	<div class="text-center">
		<h1 class="text-2xl font-bold text-gray-900 mb-4">POC Roll Call Mobile UI</h1>
		<p class="text-gray-600">Redirecting to roll call list...</p>
	</div>
</div>
