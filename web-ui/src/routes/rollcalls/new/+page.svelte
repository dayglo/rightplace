<script lang="ts">
	import type { PageData } from './$types';
	import {
		generateRollCall,
		createRollCall,
		getBatchExpectedCounts,
		type GeneratedRollCallResponse
	} from '$lib/services/api';
	import { goto } from '$app/navigation';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// Form state
	let name = $state('');
	let scheduled_at = $state('');
	let officer_id = $state('');
	let notes = $state('');
	let selectedLocationIds = $state<string[]>([]);
	let includeEmpty = $state(true);

	// Search and filter state
	let searchQuery = $state('');
	let selectedType = $state<string>('all');

	// Expected prisoner counts (schedule-aware)
	let expectedCounts = $state<Record<string, number>>({});
	let isLoadingCounts = $state(false);

	// Generated route state
	let generatedRoute: GeneratedRollCallResponse | null = $state(null);
	let isGenerating = $state(false);
	let isCreating = $state(false);
	let error = $state('');

	// Calculate default scheduled time (tomorrow at 9:00 AM)
	$effect(() => {
		if (!scheduled_at) {
			const tomorrow = new Date();
			tomorrow.setDate(tomorrow.getDate() + 1);
			tomorrow.setHours(9, 0, 0, 0);
			scheduled_at = tomorrow.toISOString().slice(0, 16);
		}
	});

	// Fetch schedule-aware counts when scheduled_at changes
	$effect(() => {
		if (scheduled_at) {
			fetchExpectedCounts();
		}
	});

	async function fetchExpectedCounts() {
		if (!scheduled_at) return;

		isLoadingCounts = true;
		try {
			// Get all unique location IDs
			const locationIds = data.locations.map((loc) => loc.id);

			// Fetch counts in one batch API call
			const response = await getBatchExpectedCounts(locationIds, scheduled_at);
			expectedCounts = response.counts;
		} catch (err) {
			console.error('Failed to fetch expected counts:', err);
			expectedCounts = {};
		} finally {
			isLoadingCounts = false;
		}
	}

	// Get all descendant location IDs (including the location itself)
	function getDescendantLocationIds(locationId: string): string[] {
		const descendants = [locationId];
		const queue = [locationId];

		while (queue.length > 0) {
			const currentId = queue.shift()!;
			const children = data.locations.filter((loc) => loc.parent_id === currentId);

			for (const child of children) {
				descendants.push(child.id);
				queue.push(child.id);
			}
		}

		return descendants;
	}

	// Get inmates count for a location at the scheduled time
	// Uses schedule-aware counts from API, falls back to home cell count
	function getInmatesAtLocation(locationId: string): number {
		// If we have schedule-aware counts, use them
		if (expectedCounts[locationId] !== undefined) {
			return expectedCounts[locationId];
		}

		// Fallback: calculate from home cell assignments
		const locationIds = getDescendantLocationIds(locationId);
		return data.inmates.filter((inmate) => locationIds.includes(inmate.home_cell_id)).length;
	}

	// Get location by ID
	function getLocation(id: string) {
		return data.locations.find((loc) => loc.id === id);
	}

	// Toggle location selection
	function toggleLocation(locationId: string) {
		if (selectedLocationIds.includes(locationId)) {
			selectedLocationIds = selectedLocationIds.filter((id) => id !== locationId);
		} else {
			selectedLocationIds = [...selectedLocationIds, locationId];
		}
		// Clear generated route when selection changes
		generatedRoute = null;
	}

	// Select all filtered locations
	function selectAllFiltered() {
		const allFilteredIds = filteredLocations.map((loc) => loc.id);
		selectedLocationIds = [...new Set([...selectedLocationIds, ...allFilteredIds])];
		generatedRoute = null;
	}

	// Clear all selected locations
	function clearAll() {
		selectedLocationIds = [];
		generatedRoute = null;
	}

	// Handle route generation
	async function handleGenerateRoute(e: Event) {
		e.preventDefault();
		error = '';

		// Validation
		if (!scheduled_at) {
			error = 'Scheduled time is required';
			return;
		}

		if (selectedLocationIds.length === 0) {
			error = 'Please select at least one location';
			return;
		}

		isGenerating = true;

		try {
			generatedRoute = await generateRollCall({
				location_ids: selectedLocationIds,
				scheduled_at,
				include_empty: includeEmpty,
				name: name.trim() || undefined,
				officer_id: officer_id.trim() || undefined
			});
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to generate route';
			generatedRoute = null;
		} finally {
			isGenerating = false;
		}
	}

	// Handle final roll call creation
	async function handleCreateRollCall(e: Event) {
		e.preventDefault();
		error = '';

		if (!generatedRoute) {
			error = 'Please generate a route first';
			return;
		}

		if (!name.trim()) {
			error = 'Roll call name is required';
			return;
		}

		isCreating = true;

		try {
			// Convert generated route to create request format
			const route = generatedRoute.route.map((stop, index) => {
				const expectedInmates = data.inmates
					.filter((inmate) => inmate.home_cell_id === stop.location_id)
					.map((inmate) => inmate.id);

				return {
					id: `stop-${index + 1}`,
					location_id: stop.location_id,
					order: stop.order,
					expected_inmates: expectedInmates,
					status: 'pending' as const
				};
			});

			// Create roll call
			const rollCall = await createRollCall({
				name: name.trim(),
				scheduled_at: scheduled_at,
				officer_id: officer_id.trim() || 'OFFICER001',
				route,
				notes: notes.trim() || ''
			});

			// Navigate to the created roll call
			goto(`/rollcalls/${rollCall.id}`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create roll call';
			isCreating = false;
		}
	}

	// Filter locations based on search query and type
	const filteredLocations = $derived.by(() => {
		let filtered = data.locations;

		// Filter by type if not "all"
		if (selectedType !== 'all') {
			filtered = filtered.filter((loc) => loc.type === selectedType);
		}

		// Filter by search query
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase();
			filtered = filtered.filter((loc) =>
				loc.name.toLowerCase().includes(query) ||
				loc.type.toLowerCase().includes(query) ||
				loc.building?.toLowerCase().includes(query)
			);
		}

		return filtered;
	});

	// Get unique location types for the filter dropdown
	const locationTypes = $derived.by(() => {
		const types = new Set(data.locations.map((loc) => loc.type));
		return Array.from(types).sort();
	});

	// Format time in minutes and seconds
	function formatTime(seconds: number): string {
		const mins = Math.floor(seconds / 60);
		const secs = seconds % 60;
		return `${mins}m ${secs}s`;
	}
</script>

<div class="min-h-screen bg-gray-50">
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Header -->
		<div class="flex justify-between items-center mb-6">
			<h1 class="text-3xl font-bold text-gray-900">Create Roll Call</h1>
			<a
				href="/rollcalls"
				class="text-gray-600 hover:text-gray-900 font-medium"
			>
				← Back
			</a>
		</div>

		<form onsubmit={generatedRoute ? handleCreateRollCall : handleGenerateRoute} class="space-y-6">
			<!-- Roll Call Details -->
			<div class="bg-white rounded-lg shadow p-6">
				<h2 class="text-xl font-semibold text-gray-900 mb-4">Roll Call Details</h2>

				<div class="space-y-4">
					<!-- Name -->
					<div>
						<label for="name" class="block text-sm font-medium text-gray-700 mb-1">
							Name *
						</label>
						<input
							type="text"
							id="name"
							bind:value={name}
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
							placeholder="Morning Roll Call - Jan 30"
							required
						/>
					</div>

					<!-- Scheduled Time -->
					<div>
						<label for="scheduled_at" class="block text-sm font-medium text-gray-700 mb-1">
							Scheduled Time *
						</label>
						<input
							type="datetime-local"
							id="scheduled_at"
							bind:value={scheduled_at}
							onchange={() => { generatedRoute = null; }}
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
							required
						/>
					</div>

					<!-- Officer ID -->
					<div>
						<label for="officer_id" class="block text-sm font-medium text-gray-700 mb-1">
							Officer ID
						</label>
						<input
							type="text"
							id="officer_id"
							bind:value={officer_id}
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
							placeholder="OFFICER001"
						/>
					</div>

					<!-- Notes -->
					<div>
						<label for="notes" class="block text-sm font-medium text-gray-700 mb-1">
							Notes
						</label>
						<textarea
							id="notes"
							bind:value={notes}
							rows="3"
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
							placeholder="Additional notes..."
						></textarea>
					</div>

					<!-- Include Empty Cells -->
					<div class="flex items-center gap-2">
						<input
							type="checkbox"
							id="include_empty"
							bind:checked={includeEmpty}
							onchange={() => { generatedRoute = null; }}
							class="rounded"
						/>
						<label for="include_empty" class="text-sm font-medium text-gray-700">
							Include empty cells in route
						</label>
					</div>
				</div>
			</div>

			<!-- Location Selection -->
			<div class="bg-white rounded-lg shadow p-6">
				<div class="flex items-center justify-between mb-4">
					<h2 class="text-xl font-semibold text-gray-900">Select Locations</h2>
					{#if isLoadingCounts}
						<span class="text-sm text-blue-600">Calculating expected counts...</span>
					{:else if Object.keys(expectedCounts).length > 0}
						<span class="text-sm text-green-600">✓ Schedule-aware counts loaded</span>
					{/if}
				</div>
				<p class="text-sm text-gray-600 mb-4">
					Counts show prisoners expected at each location at the scheduled time, based on their schedules.
				</p>

				<!-- Search and Filter Controls -->
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
					<!-- Search Input -->
					<div>
						<label for="location-search" class="block text-sm font-medium text-gray-700 mb-1">
							Search by name
						</label>
						<input
							type="text"
							id="location-search"
							bind:value={searchQuery}
							placeholder="Search locations..."
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>

					<!-- Type Filter Dropdown -->
					<div>
						<label for="type-filter" class="block text-sm font-medium text-gray-700 mb-1">
							Filter by type
						</label>
						<select
							id="type-filter"
							bind:value={selectedType}
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						>
							<option value="all">All types</option>
							{#each locationTypes as type (type)}
								<option value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
							{/each}
						</select>
					</div>
				</div>

				<!-- Quick Actions -->
				<div class="flex gap-2 mb-4">
					<button
						type="button"
						onclick={selectAllFiltered}
						disabled={filteredLocations.length === 0}
						class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						Select All ({filteredLocations.length})
					</button>
					<button
						type="button"
						onclick={clearAll}
						disabled={selectedLocationIds.length === 0}
						class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						Clear All
					</button>
				</div>

				<div class="border border-gray-300 rounded-lg p-4 max-h-96 overflow-y-auto">
					{#if filteredLocations.length === 0}
						<p class="text-gray-500 text-sm">No locations match your search</p>
					{:else}
						<div class="space-y-2">
							{#each filteredLocations as location (location.id)}
								{@const inmatesCount = getInmatesAtLocation(location.id)}
								<label class="flex items-start gap-3 p-2 hover:bg-gray-50 rounded cursor-pointer">
									<input
										type="checkbox"
										checked={selectedLocationIds.includes(location.id)}
										onchange={() => toggleLocation(location.id)}
										class="mt-1"
									/>
									<div class="flex-1">
										<div class="flex items-center gap-2">
											<span class="font-medium text-gray-900">{location.name}</span>
											<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
												{location.type}
											</span>
										</div>
										<div class="text-sm text-gray-600">
											{inmatesCount} {inmatesCount === 1 ? 'prisoner' : 'prisoners'}
											{#if expectedCounts[location.id] !== undefined}
												<span class="text-green-600">(expected)</span>
											{:else}
												<span class="text-gray-500">(home cell)</span>
											{/if}
										</div>
									</div>
								</label>
							{/each}
						</div>
					{/if}
				</div>

				<div class="mt-4 text-sm text-gray-600">
					Selected: {selectedLocationIds.length} {selectedLocationIds.length === 1 ? 'location' : 'locations'}
				</div>
			</div>

			<!-- Generated Route Preview -->
			{#if generatedRoute}
				<div class="bg-white rounded-lg shadow p-6 border-2 border-green-200">
					<h2 class="text-xl font-semibold text-gray-900 mb-4">Generated Route</h2>

					<!-- Summary Stats -->
					<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
						<div class="bg-blue-50 rounded-lg p-4">
							<div class="text-2xl font-bold text-blue-900">{generatedRoute.summary.total_locations}</div>
							<div class="text-sm text-blue-700">Total Stops</div>
						</div>
						<div class="bg-green-50 rounded-lg p-4">
							<div class="text-2xl font-bold text-green-900">{generatedRoute.summary.total_prisoners_expected}</div>
							<div class="text-sm text-green-700">Expected Prisoners</div>
						</div>
						<div class="bg-purple-50 rounded-lg p-4">
							<div class="text-2xl font-bold text-purple-900">{generatedRoute.summary.occupied_locations}</div>
							<div class="text-sm text-purple-700">Occupied Cells</div>
						</div>
						<div class="bg-orange-50 rounded-lg p-4">
							<div class="text-2xl font-bold text-orange-900">{formatTime(generatedRoute.summary.estimated_time_seconds)}</div>
							<div class="text-sm text-orange-700">Est. Time</div>
						</div>
					</div>

					<!-- Route Stops -->
					<h3 class="font-semibold text-gray-900 mb-3">Optimized Route</h3>
					<div class="space-y-2 max-h-96 overflow-y-auto">
						{#each generatedRoute.route as stop (stop.location_id)}
							<div class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
								<div class="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-semibold">
									{stop.order}
								</div>
								<div class="flex-1">
									<div class="font-medium text-gray-900">{stop.location_name}</div>
									<div class="text-sm text-gray-600">
										{stop.expected_count} {stop.expected_count === 1 ? 'prisoner' : 'prisoners'}
										{#if stop.walking_distance_meters > 0}
											• {stop.walking_distance_meters}m • {stop.walking_time_seconds}s walk
										{/if}
									</div>
								</div>
								<div class="flex-shrink-0">
									{#if stop.is_occupied}
										<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
											Occupied
										</span>
									{:else}
										<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
											Empty
										</span>
									{/if}
								</div>
							</div>
						{/each}
					</div>

					<button
						type="button"
						onclick={() => { generatedRoute = null; }}
						class="mt-4 text-sm text-blue-600 hover:text-blue-800 font-medium"
					>
						← Modify Selection
					</button>
				</div>
			{/if}

			<!-- Error Message -->
			{#if error}
				<div class="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
					{error}
				</div>
			{/if}

			<!-- Actions -->
			<div class="flex justify-between">
				<a
					href="/rollcalls"
					class="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium"
				>
					Cancel
				</a>
				{#if generatedRoute}
					<button
						type="submit"
						disabled={isCreating}
						class="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{isCreating ? 'Creating...' : 'Create Roll Call'}
					</button>
				{:else}
					<button
						type="submit"
						disabled={isGenerating || selectedLocationIds.length === 0}
						class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{isGenerating ? 'Generating...' : 'Generate Route'}
					</button>
				{/if}
			</div>
		</form>
	</main>
</div>
