<script lang="ts">
	import type { PageData } from './$types';
	import LocationCard from '$lib/components/LocationCard.svelte';
	import { deleteLocation } from '$lib/services/api';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let filterType = $state<string>('all');
	let filterBuilding = $state<string>('all');

	// Get unique buildings for filter
	const buildings = $derived(() => {
		const uniqueBuildings = new Set(data.locations.map((loc) => loc.building));
		return Array.from(uniqueBuildings).sort();
	});

	// Filter locations
	const filteredLocations = $derived(() => {
		let result = data.locations;

		// Filter by type
		if (filterType !== 'all') {
			result = result.filter((loc) => loc.type === filterType);
		}

		// Filter by building
		if (filterBuilding !== 'all') {
			result = result.filter((loc) => loc.building === filterBuilding);
		}

		return result;
	});

	// Get parent location name
	function getParentName(parentId?: string): string | undefined {
		if (!parentId) return undefined;
		const parent = data.locations.find((loc) => loc.id === parentId);
		return parent?.name;
	}

	// Handle delete
	async function handleDelete(locationId: string) {
		if (!confirm('Are you sure you want to delete this location?')) {
			return;
		}

		try {
			await deleteLocation(locationId);
			// Reload page by refreshing
			window.location.reload();
		} catch (error) {
			alert(error instanceof Error ? error.message : 'Failed to delete location');
		}
	}

	// Handle edit (navigate to edit page - not yet implemented)
	function handleEdit(locationId: string) {
		// TODO: Implement edit page
		alert('Edit functionality coming soon');
	}
</script>

<div class="min-h-screen bg-gray-50">
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Header -->
		<div class="flex justify-between items-center mb-6">
			<h1 class="text-3xl font-bold text-gray-900">Locations</h1>
			<a
				href="/locations/new"
				class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
			>
				+ Add Location
			</a>
		</div>

		<!-- Filters -->
		<div class="bg-white rounded-lg shadow p-6 mb-6">
			<div class="flex flex-col sm:flex-row gap-4">
				<select
					bind:value={filterType}
					class="border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<option value="all">All Types</option>
					<optgroup label="Accommodation">
						<option value="houseblock">Houseblocks</option>
						<option value="wing">Wings</option>
						<option value="landing">Landings</option>
						<option value="cell">Cells</option>
					</optgroup>
					<optgroup label="Special Units">
						<option value="healthcare">Healthcare</option>
						<option value="segregation">Segregation</option>
						<option value="vpu">VPU</option>
						<option value="induction">Induction</option>
					</optgroup>
					<optgroup label="Facilities">
						<option value="education">Education</option>
						<option value="workshop">Workshops</option>
						<option value="gym">Gym</option>
						<option value="chapel">Chapel</option>
						<option value="visits">Visits</option>
						<option value="reception">Reception</option>
						<option value="kitchen">Kitchen</option>
						<option value="yard">Yards</option>
						<option value="admin">Admin</option>
					</optgroup>
				</select>

				<select
					bind:value={filterBuilding}
					class="border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<option value="all">All Buildings</option>
					{#each buildings() as building}
						<option value={building}>{building}</option>
					{/each}
				</select>
			</div>

			<!-- Stats -->
			<div class="mt-4 flex gap-6 text-sm text-gray-600">
				<span>Total: {data.locations.length}</span>
			</div>
		</div>

		<!-- Location List -->
		{#if filteredLocations().length === 0}
			<div class="bg-white rounded-lg shadow p-12 text-center">
				<p class="text-gray-500 text-lg">No locations found</p>
			</div>
		{:else}
			<div class="space-y-4">
				{#each filteredLocations() as location (location.id)}
					<LocationCard
						{location}
						parentName={getParentName(location.parent_id)}
						onEdit={() => handleEdit(location.id)}
						onDelete={() => handleDelete(location.id)}
					/>
				{/each}
			</div>
		{/if}
	</main>
</div>
