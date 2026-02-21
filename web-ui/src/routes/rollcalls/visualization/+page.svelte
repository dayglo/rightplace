<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { treemapStore, currentZoomNode, type DateRangePreset } from '$lib/stores/treemapStore';
	import ZoomableTreemap from '$lib/components/rollcall/ZoomableTreemap.svelte';
	import CirclePacking from '$lib/components/rollcall/CirclePacking.svelte';
	// import TimelineStrip from '$lib/components/rollcall/TimelineStrip.svelte';

	let loading = false;
	let error: string | null = null;
	let activeView: 'treemap' | 'circle' | 'both' = 'circle';
	let playInterval: ReturnType<typeof setInterval> | null = null;
	let liveInterval: ReturnType<typeof setInterval> | null = null;

	// Cache settings
	let cacheRangeHours = 12;
	let cacheStepMinutes = 15;

	// Computed cache info
	$: cacheEntryCount = Math.ceil((cacheRangeHours * 2 * 60) / cacheStepMinutes);

	// Load data on mount
	onMount(async () => {
		loading = true;
		try {
			await treemapStore.fetchPrisons();
			await treemapStore.fetchRollcalls();
			await treemapStore.fetchData();
			// Start background prefetch
			treemapStore.prefetchCache();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load data';
		} finally {
			loading = false;
		}
	});

	// Cleanup intervals on destroy
	onDestroy(() => {
		if (playInterval) clearInterval(playInterval);
		if (liveInterval) clearInterval(liveInterval);
	});

	// Handle playback - use cache when available
	$: if ($treemapStore.isPlaying && !playInterval) {
		playInterval = setInterval(() => {
			// Calculate step: 0 = realtime (playbackSpeed ms = same in sim), otherwise use playbackStepSeconds
			const stepSeconds = $treemapStore.playbackStepSeconds === 0
				? $treemapStore.playbackSpeed / 1000  // Realtime: 3 sec real = 3 sec sim
				: $treemapStore.playbackStepSeconds;
			const stepMinutes = stepSeconds / 60;
			treemapStore.stepForward(stepMinutes);
			const cached = treemapStore.getDataForTimestamp($treemapStore.timestamp);
			if (cached) {
				treemapStore.setData(cached);
			} else {
				treemapStore.fetchData();
			}
		}, $treemapStore.playbackSpeed);
	} else if (!$treemapStore.isPlaying && playInterval) {
		clearInterval(playInterval);
		playInterval = null;
	}

	// Handle live mode
	$: if ($treemapStore.liveMode && !liveInterval) {
		liveInterval = setInterval(() => {
			treemapStore.setTimestamp(new Date());
			treemapStore.fetchData();
		}, 5000);
	} else if (!$treemapStore.liveMode && liveInterval) {
		clearInterval(liveInterval);
		liveInterval = null;
	}

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
			treemapStore.setTimestamp(new Date());
			treemapStore.fetchData();
		}
	}

	function handleToggleEmpty() {
		treemapStore.toggleIncludeEmpty();
		treemapStore.fetchData();
		treemapStore.invalidateCache();
		treemapStore.prefetchCache();
	}

	function handleToggleFilterToRoute() {
		treemapStore.toggleFilterToRoute();
		treemapStore.fetchData();
		treemapStore.invalidateCache();
		treemapStore.prefetchCache();
	}

	function handleOccupancyModeChange(event: Event) {
		const mode = (event.target as HTMLSelectElement).value as 'scheduled' | 'home_cell';
		treemapStore.setOccupancyMode(mode);
		treemapStore.fetchData();
		treemapStore.invalidateCache();
		treemapStore.prefetchCache();
	}

	function handlePrisonToggle(prisonId: string) {
		const current = $treemapStore.selectedPrisonIds;
		let updated: string[];
		if (current.includes(prisonId)) {
			updated = current.filter(id => id !== prisonId);
			if (updated.length === 0) return;
		} else {
			updated = [...current, prisonId];
		}
		treemapStore.setSelectedPrisons(updated);
		treemapStore.fetchData();
		treemapStore.invalidateCache();
		treemapStore.prefetchCache();
	}

	function handleZoomOut() {
		treemapStore.zoomOut();
	}

	function handleTimestampChange(event: CustomEvent<Date>) {
		treemapStore.setTimestamp(event.detail);
		treemapStore.fetchData();
	}

	function handleRangeChange(event: CustomEvent<DateRangePreset>) {
		treemapStore.setDateRangePreset(event.detail);
	}

	function handleStep(event: CustomEvent<number>) {
		if (event.detail > 0) {
			treemapStore.stepForward();
		} else {
			treemapStore.stepBackward();
		}
		treemapStore.fetchData();
	}

	function handleSkip(event: CustomEvent<number>) {
		if (event.detail > 0) {
			treemapStore.skipForward();
		} else {
			treemapStore.skipBackward();
		}
		treemapStore.fetchData();
	}

	function handleTogglePlay() {
		treemapStore.togglePlayback();
	}

	function handleCacheConfigChange() {
		treemapStore.setCacheConfig(cacheRangeHours, cacheStepMinutes);
		treemapStore.invalidateCache();
		treemapStore.prefetchCache();
	}

	function handleRollcallToggle(rollcallId: string) {
		const current = $treemapStore.selectedRollcallIds;
		let updated: string[];
		if (current.includes(rollcallId)) {
			// Remove this rollcall
			updated = current.filter(id => id !== rollcallId);
		} else {
			// Add this rollcall
			updated = [...current, rollcallId];
		}
		treemapStore.setRollcalls(updated);
		treemapStore.fetchData();
		treemapStore.invalidateCache();
		treemapStore.prefetchCache();
	}

	function formatRollcallLabel(rc: any): string {
		const time = new Date(rc.scheduled_at).toLocaleTimeString('en-GB', {
			hour: '2-digit',
			minute: '2-digit'
		});
		const statusEmoji = rc.status === 'completed' ? '✓' : rc.status === 'in_progress' ? '▶' : '○';
		return `${statusEmoji} ${rc.name} (${time})`;
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
			<!-- Prison Multi-Select -->
			<div class="flex items-center gap-2">
				<label class="text-sm text-gray-700 font-medium">Prisons:</label>
				<div class="flex gap-1 flex-wrap">
					{#each $treemapStore.availablePrisons as prison}
						<button
							on:click={() => handlePrisonToggle(prison.id)}
							class="px-2 py-1 text-xs rounded border transition-colors {$treemapStore.selectedPrisonIds.includes(prison.id)
								? 'bg-blue-600 text-white border-blue-600'
								: 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'}"
						>
							{prison.name.replace('HMP ', '')}
						</button>
					{/each}
				</div>
			</div>

			<div class="w-px h-6 bg-gray-300"></div>

			<!-- Rollcall Multi-Select -->
			<div class="flex items-center gap-2">
				<label class="text-sm text-gray-700 font-medium">Rollcalls:</label>
				{#if $treemapStore.rollcallsLoading}
					<span class="text-xs text-gray-500">Loading...</span>
				{:else if $treemapStore.availableRollcalls.length === 0}
					<span class="text-xs text-gray-500">No rollcalls found</span>
				{:else}
					<div class="flex gap-1 flex-wrap max-w-2xl">
						<button
							on:click={() => {
								const allIds = $treemapStore.availableRollcalls.map(rc => rc.id);
								treemapStore.setRollcalls(allIds);
								treemapStore.fetchData();
								treemapStore.invalidateCache();
								treemapStore.prefetchCache();
							}}
							class="px-2 py-1 text-xs rounded border transition-colors {$treemapStore.selectedRollcallIds.length === $treemapStore.availableRollcalls.length && $treemapStore.availableRollcalls.length > 0
								? 'bg-purple-600 text-white border-purple-600'
								: 'bg-white text-gray-700 border-gray-300 hover:border-purple-400'}"
							title="Show all rollcalls combined"
						>
							All
						</button>
						{#each $treemapStore.availableRollcalls.slice(0, 15) as rollcall}
							<button
								on:click={() => handleRollcallToggle(rollcall.id)}
								class="px-2 py-1 text-xs rounded border transition-colors {$treemapStore.selectedRollcallIds.includes(rollcall.id)
									? 'bg-green-600 text-white border-green-600'
									: 'bg-white text-gray-700 border-gray-300 hover:border-green-400'}"
								title={rollcall.name}
							>
								{formatRollcallLabel(rollcall)}
							</button>
						{/each}
					</div>
				{/if}
			</div>

			<div class="w-px h-6 bg-gray-300"></div>

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

			<div class="flex items-center gap-2">
				<input
					type="checkbox"
					id="filter-to-route"
					checked={$treemapStore.filterToRoute}
					on:change={handleToggleFilterToRoute}
					class="w-4 h-4"
				/>
				<label for="filter-to-route" class="text-sm text-gray-700">
					Focus on selected rollcall
				</label>
			</div>
		</div>

		<!-- Cache Settings (collapsible) -->
		<details class="bg-gray-50 p-3 rounded-lg mt-4">
			<summary class="text-sm font-medium cursor-pointer flex items-center gap-2">
				Cache Settings
				<span class="text-gray-500 text-xs">
					({#if $treemapStore.cacheStatus === 'ready'}Ready
					{:else if $treemapStore.cacheStatus === 'loading'}Loading {$treemapStore.cacheProgress}%
					{:else if $treemapStore.cacheStatus === 'error'}Error
					{:else}Not loaded{/if})
				</span>
			</summary>
			<div class="mt-3 flex gap-4 items-center flex-wrap">
				<label class="text-sm flex items-center gap-2">
					Range:
					<select bind:value={cacheRangeHours} on:change={handleCacheConfigChange} class="px-2 py-1 border rounded text-sm bg-white">
						<option value={1}>+/-1h</option>
						<option value={6}>+/-6h</option>
						<option value={12}>+/-12h</option>
						<option value={24}>+/-24h</option>
					</select>
				</label>
				<label class="text-sm flex items-center gap-2">
					Step:
					<select bind:value={cacheStepMinutes} on:change={handleCacheConfigChange} class="px-2 py-1 border rounded text-sm bg-white">
						<option value={5}>5 min</option>
						<option value={15}>15 min</option>
						<option value={30}>30 min</option>
						<option value={60}>1 hour</option>
					</select>
				</label>
				<button
					on:click={() => { treemapStore.invalidateCache(); treemapStore.prefetchCache(); }}
					class="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 text-blue-700 rounded transition"
				>
					Refresh Cache
				</button>
				<span class="text-xs text-gray-500">{cacheEntryCount} entries</span>
				{#if $treemapStore.cacheStatus === 'loading'}
					<div class="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
						<div class="h-full bg-blue-500 transition-all" style="width: {$treemapStore.cacheProgress}%"></div>
					</div>
				{/if}
			</div>
		</details>
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

	<!-- Prominent Timestamp Display -->
	<div class="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg p-6 mb-6 text-center shadow-lg">
		<div class="text-sm uppercase tracking-wider opacity-90 mb-2">Viewing Time</div>
		<div class="text-5xl font-bold mb-1">
			{$treemapStore.timestamp.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
		</div>
		<div class="text-xl opacity-90">
			{$treemapStore.timestamp.toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
		</div>
	</div>

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
					{$treemapStore.occupancyMode === 'scheduled' ? 'Scheduled' : 'Home Cell'}
				</div>
			</div>
		</div>
	{/if}

	<!-- Timeline Strip - Simple controls with date-time picker -->
	<div class="mt-6 rounded-lg overflow-hidden shadow-lg bg-gray-800 p-4">
		<div class="flex gap-4 items-center justify-center text-white flex-wrap">
			<button
				on:click={() => { treemapStore.skipBackward(); treemapStore.fetchRollcalls(); treemapStore.fetchData(); }}
				class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded"
			>
				⏪ -1h
			</button>
			<button
				on:click={() => { treemapStore.stepBackward(); treemapStore.fetchRollcalls(); treemapStore.fetchData(); }}
				class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded"
			>
				◀ -15min
			</button>
			<button
				on:click={handleTogglePlay}
				class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded font-bold"
			>
				{$treemapStore.isPlaying ? '⏸ Pause' : '▶ Play'}
			</button>
			<select
				value={$treemapStore.playbackStepSeconds}
				on:change={(e) => treemapStore.setPlaybackStep(parseInt(e.currentTarget.value))}
				class="px-2 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm"
				title="Playback speed - simulation time per tick"
			>
				<option value={0}>Realtime</option>
				<option value={10}>10 sec</option>
				<option value={30}>30 sec</option>
				<option value={60}>1 min</option>
				<option value={120}>2 min</option>
				<option value={300}>5 min</option>
				<option value={600}>10 min</option>
			</select>
			<button
				on:click={() => { treemapStore.stepForward(); treemapStore.fetchRollcalls(); treemapStore.fetchData(); }}
				class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded"
			>
				+15min ▶
			</button>
			<button
				on:click={() => { treemapStore.skipForward(); treemapStore.fetchRollcalls(); treemapStore.fetchData(); }}
				class="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded"
			>
				+1h ⏩
			</button>
			<div class="ml-4 flex items-center gap-2">
				<input
					type="datetime-local"
					value={$treemapStore.timestamp.toISOString().slice(0, 16)}
					on:change={(e) => {
						const newDate = new Date(e.currentTarget.value);
						treemapStore.setTimestamp(newDate);
						treemapStore.fetchRollcalls(); // Update available rollcalls for new timestamp
						treemapStore.fetchData();
					}}
					class="px-3 py-1 bg-gray-900 border border-gray-600 rounded text-white text-sm"
				/>
			</div>
			<div class="text-sm text-gray-300">
				{$treemapStore.timestamp.toLocaleString()}
			</div>
		</div>
	</div>

	<!-- Debug Panel -->
	<details class="mt-6 bg-gray-900 text-green-400 rounded-lg text-xs font-mono">
		<summary class="px-3 py-2 cursor-pointer hover:bg-gray-800 rounded-t-lg">Debug Panel</summary>
		<div class="p-3 border-t border-gray-700 grid grid-cols-2 gap-4">
			<div>
				<div class="text-gray-500 mb-1">CACHE</div>
				<div class="space-y-1">
					<div>Status: <span class="{$treemapStore.cacheStatus === 'ready' ? 'text-green-400' : $treemapStore.cacheStatus === 'loading' ? 'text-yellow-400' : 'text-gray-400'}">{$treemapStore.cacheStatus}</span></div>
					<div>Entries: {$treemapStore.timestampCache.size}</div>
					<div>Range: +/-{$treemapStore.cacheRangeHours}h @ {$treemapStore.cacheStepMinutes}min</div>
					{#if $treemapStore.cacheStatus === 'loading'}
						<div>Progress: {$treemapStore.cacheProgress}%</div>
					{/if}
					<div>Current: <span class="{treemapStore.getDataForTimestamp($treemapStore.timestamp) ? 'text-green-400' : 'text-red-400'}">{treemapStore.getDataForTimestamp($treemapStore.timestamp) ? 'HIT' : 'MISS'}</span></div>
				</div>
			</div>
			<div>
				<div class="text-gray-500 mb-1">STATE</div>
				<div class="space-y-1">
					<div>Loading: <span class="{loading ? 'text-yellow-400' : 'text-gray-400'}">{loading}</span></div>
					<div>Playing: <span class="{$treemapStore.isPlaying ? 'text-green-400' : 'text-gray-400'}">{$treemapStore.isPlaying}</span></div>
					<div>Live: <span class="{$treemapStore.liveMode ? 'text-green-400' : 'text-gray-400'}">{$treemapStore.liveMode}</span></div>
					<div>Time: {$treemapStore.timestamp.toISOString().slice(11, 19)}</div>
					<div>Inmates: {$treemapStore.data?.value ?? 0}</div>
					<div>Prisons: {$treemapStore.selectedPrisonIds.length}/{$treemapStore.availablePrisons.length}</div>
					<div>Zoom: {$treemapStore.zoomPath.length} deep</div>
				</div>
			</div>
		</div>
	</details>
</div>
