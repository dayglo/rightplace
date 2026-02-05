<script lang="ts">
	import { onMount } from 'svelte';
	import { treemapStore, currentZoomNode } from '$lib/stores/treemapStore';
	import ZoomableTreemap from '$lib/components/rollcall/ZoomableTreemap.svelte';
	import CirclePacking from '$lib/components/rollcall/CirclePacking.svelte';

	let loading = false;
	let error: string | null = null;
	let activeView: 'treemap' | 'circle' | 'both' = 'circle';

	// Load data on mount
	onMount(async () => {
		loading = true;
		try {
			await treemapStore.fetchData();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load data';
		} finally {
			loading = false;
		}
	});

	function handleNodeClick(node: any) {
		if (node.children && node.children.length > 0) {
			treemapStore.zoomTo(node);
		}
	}

	function handleRefresh() {
		treemapStore.fetchData();
	}

	function handleToggleLive() {
		treemapStore.toggleLiveMode();
		if ($treemapStore.liveMode) {
			// Update every 5 seconds in live mode
			const interval = setInterval(() => {
				if ($treemapStore.liveMode) {
					treemapStore.setTimestamp(new Date());
					treemapStore.fetchData();
				} else {
					clearInterval(interval);
				}
			}, 5000);
		}
	}

	function handleToggleEmpty() {
		treemapStore.toggleIncludeEmpty();
		treemapStore.fetchData();
	}

	function handleOccupancyModeChange(event: Event) {
		const mode = (event.target as HTMLSelectElement).value as 'scheduled' | 'home_cell';
		treemapStore.setOccupancyMode(mode);
		treemapStore.fetchData();
	}

	function handleZoomOut() {
		treemapStore.zoomOut();
	}

	$: breadcrumb = $treemapStore.zoomPath.map(n => n.name).join(' > ') || 'All Facilities';
</script>

<svelte:head>
	<title>Roll Call Visualization | Prison Roll Call</title>
</svelte:head>

<div class="container mx-auto px-4 py-8">
	<!-- Header -->
	<div class="mb-6">
		<div class="flex justify-between items-center mb-4">
			<h1 class="text-3xl font-bold text-gray-900">Roll Call Visualization</h1>
			<div class="flex gap-2">
				<a
					href="/rollcalls"
					class="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition"
				>
					← Back to Roll Calls
				</a>
				<button
					on:click={handleRefresh}
					disabled={loading}
					class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50"
				>
					🔄 Refresh
				</button>
				<button
					on:click={handleToggleLive}
					class="px-4 py-2 text-sm {$treemapStore.liveMode ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-600 hover:bg-gray-700'} text-white rounded-lg transition"
				>
					{$treemapStore.liveMode ? '🔴 LIVE' : '⚡ Start Live'}
				</button>
			</div>
		</div>

		<!-- Breadcrumb -->
		<div class="flex items-center gap-2 text-sm text-gray-600 mb-4">
			<button
				on:click={() => treemapStore.zoomToRoot()}
				class="hover:text-blue-600 transition"
			>
				🏠 {breadcrumb}
			</button>
		</div>

		<!-- Controls -->
		<div class="flex gap-4 items-center bg-gray-50 p-4 rounded-lg flex-wrap">
			<div class="flex items-center gap-2">
				<label class="text-sm text-gray-700">View:</label>
				<select
					bind:value={activeView}
					class="px-3 py-1 border rounded text-sm bg-white"
				>
					<option value="treemap">Treemap Only</option>
					<option value="circle">Circle Packing Only</option>
					<option value="both">Both Views</option>
				</select>
			</div>

			<div class="flex items-center gap-2">
				<label class="text-sm text-gray-700">Timestamp:</label>
				<input
					type="datetime-local"
					value={$treemapStore.timestamp.toISOString().slice(0, 16)}
					on:change={(e) => {
						const date = new Date(e.currentTarget.value);
						treemapStore.setTimestamp(date);
						treemapStore.fetchData();
					}}
					class="px-3 py-1 border rounded text-sm"
					disabled={$treemapStore.liveMode}
				/>
			</div>

			<div class="flex items-center gap-2">
				<label class="text-sm text-gray-700">Occupancy:</label>
				<select
					value={$treemapStore.occupancyMode}
					on:change={handleOccupancyModeChange}
					class="px-3 py-1 border rounded text-sm bg-white"
				>
					<option value="scheduled">Scheduled Location</option>
					<option value="home_cell">Home Cell</option>
				</select>
			</div>

			<div class="flex items-center gap-2">
				<input
					type="checkbox"
					id="include-empty"
					checked={$treemapStore.includeEmpty}
					on:change={handleToggleEmpty}
					class="w-4 h-4"
				/>
				<label for="include-empty" class="text-sm text-gray-700">
					Include empty locations
				</label>
			</div>
		</div>
	</div>

	<!-- Legend -->
	<div class="mb-6 bg-white p-4 rounded-lg shadow-sm">
		<h3 class="text-sm font-semibold text-gray-700 mb-2">Status Legend:</h3>
		<div class="flex gap-6 text-sm">
			<div class="flex items-center gap-2">
				<div class="w-4 h-4 bg-gray-500 rounded"></div>
				<span>Grey: No rollcall scheduled</span>
			</div>
			<div class="flex items-center gap-2">
				<div class="w-4 h-4 bg-amber-500 rounded"></div>
				<span>Amber: Scheduled, not completed</span>
			</div>
			<div class="flex items-center gap-2">
				<div class="w-4 h-4 bg-emerald-500 rounded"></div>
				<span>Green: All verified</span>
			</div>
			<div class="flex items-center gap-2">
				<div class="w-4 h-4 bg-red-500 rounded"></div>
				<span>Red: Verification failed</span>
			</div>
		</div>
	</div>

	<!-- Loading State -->
	{#if loading && !$treemapStore.data}
		<div class="flex justify-center items-center h-96">
			<div class="text-center">
				<div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
				<p class="text-gray-600">Loading treemap data...</p>
			</div>
		</div>
	{/if}

	<!-- Error State -->
	{#if error}
		<div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
			<p class="text-red-800">Error: {error}</p>
		</div>
	{/if}

	<!-- Visualizations -->
	{#if $currentZoomNode}
		{#if activeView === 'both'}
			<div class="grid grid-cols-2 gap-6">
				<div class="bg-white rounded-lg shadow-lg overflow-hidden" style="height: 800px;">
					<div class="bg-gray-800 text-white px-4 py-2 text-sm font-semibold">
						Treemap View
					</div>
					<div style="height: calc(100% - 40px);">
						<ZoomableTreemap
							data={$currentZoomNode}
							onNodeClick={handleNodeClick}
						/>
					</div>
				</div>
				<div class="bg-white rounded-lg shadow-lg overflow-hidden" style="height: 800px;">
					<div class="bg-gray-800 text-white px-4 py-2 text-sm font-semibold">
						Circle Packing View
					</div>
					<div style="height: calc(100% - 40px);">
						<CirclePacking
							data={$currentZoomNode}
							onNodeClick={handleNodeClick}
							onZoomOut={handleZoomOut}
						/>
					</div>
				</div>
			</div>
		{:else if activeView === 'treemap'}
			<div class="bg-white rounded-lg shadow-lg overflow-hidden" style="height: 800px;">
				<div class="bg-gray-800 text-white px-4 py-2 text-sm font-semibold">
					Treemap View
				</div>
				<div style="height: calc(100% - 40px);">
					<ZoomableTreemap
						data={$currentZoomNode}
						onNodeClick={handleNodeClick}
					/>
				</div>
			</div>
		{:else if activeView === 'circle'}
			<div class="bg-white rounded-lg shadow-lg overflow-hidden" style="height: 800px;">
				<div class="bg-gray-800 text-white px-4 py-2 text-sm font-semibold">
					Circle Packing View
				</div>
				<div style="height: calc(100% - 40px);">
					<CirclePacking
						data={$currentZoomNode}
						onNodeClick={handleNodeClick}
						onZoomOut={handleZoomOut}
					/>
				</div>
			</div>
		{/if}
	{/if}

	<!-- Stats Panel -->
	{#if $treemapStore.data}
		<div class="mt-6 grid grid-cols-4 gap-4">
			<div class="bg-white p-4 rounded-lg shadow-sm">
				<div class="text-sm text-gray-600">Total Inmates</div>
				<div class="text-2xl font-bold text-gray-900">{$treemapStore.data.value}</div>
			</div>
			<div class="bg-white p-4 rounded-lg shadow-sm">
				<div class="text-sm text-gray-600">Facilities</div>
				<div class="text-2xl font-bold text-gray-900">{$treemapStore.data.children?.length || 0}</div>
			</div>
			<div class="bg-white p-4 rounded-lg shadow-sm">
				<div class="text-sm text-gray-600">Mode</div>
				<div class="text-2xl font-bold text-gray-900">
					{$treemapStore.selectedRollcallIds.length > 0 ? 'Rollcall' : 'Management'}
				</div>
			</div>
			<div class="bg-white p-4 rounded-lg shadow-sm">
				<div class="text-sm text-gray-600">Occupancy Mode</div>
				<div class="text-2xl font-bold text-gray-900">
					{$treemapStore.occupancyMode === 'scheduled' ? '📅 Scheduled' : '🏠 Home Cell'}
				</div>
			</div>
		</div>
	{/if}
</div>
