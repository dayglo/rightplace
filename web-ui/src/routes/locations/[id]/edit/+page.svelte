<script lang="ts">
	import { updateLocation, getLocations, type Location } from '$lib/services/api';
	import { onMount } from 'svelte';

	interface Props {
		data: {
			location: Location;
		};
	}

	let { data }: Props = $props();

	let name = $state(data.location.name);
	let locationType = $state(data.location.type);
	let building = $state(data.location.building);
	let floor = $state(data.location.floor);
	let capacity = $state(data.location.capacity);
	let parentLocationId = $state(data.location.parent_id || '');
	let isSubmitting = $state(false);
	let errorMessage = $state('');
	let availableLocations = $state<Location[]>([]);

	const locationTypes = [
		'houseblock',
		'wing',
		'landing',
		'cell',
		'healthcare',
		'segregation',
		'vpu',
		'induction',
		'education',
		'workshop',
		'gym',
		'chapel',
		'visits',
		'reception',
		'kitchen',
		'yard',
		'admin'
	];

	// Load available locations for parent dropdown (excluding current location)
	onMount(async () => {
		try {
			const locations = await getLocations();
			// Filter out current location to prevent circular reference
			availableLocations = locations.filter((loc) => loc.id !== data.location.id);
		} catch (error) {
			console.error('Failed to load locations:', error);
		}
	});

	async function handleSubmit(event: Event) {
		event.preventDefault();
		isSubmitting = true;
		errorMessage = '';

		try {
			await updateLocation(data.location.id, {
				name,
				type: locationType,
				building,
				floor,
				capacity,
				parent_id: parentLocationId || undefined
			});

			// Redirect to locations list
			window.location.href = '/locations';
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Failed to update location';
			isSubmitting = false;
		}
	}

	function handleCancel() {
		window.location.href = '/locations';
	}
</script>

<div class="min-h-screen bg-gray-50">
	<main class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Header -->
		<div class="flex items-center justify-between mb-6">
			<h1 class="text-3xl font-bold text-gray-900">Edit Location</h1>
			<a
				href="/locations"
				class="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-2"
			>
				← Back
			</a>
		</div>

		<!-- Form -->
		<div class="bg-white rounded-lg shadow p-6">
			<form onsubmit={handleSubmit}>
				<div class="space-y-6">
					<!-- Name -->
					<div>
						<label for="name" class="block text-sm font-medium text-gray-700 mb-2">
							Name *
						</label>
						<input
							type="text"
							id="name"
							bind:value={name}
							required
							placeholder="Block A"
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>

					<!-- Type -->
					<div>
						<label for="location_type" class="block text-sm font-medium text-gray-700 mb-2">
							Type *
						</label>
						<select
							id="location_type"
							bind:value={locationType}
							required
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						>
							{#each locationTypes as type}
								<option value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
							{/each}
						</select>
					</div>

					<!-- Building -->
					<div>
						<label for="building" class="block text-sm font-medium text-gray-700 mb-2">
							Building *
						</label>
						<input
							type="text"
							id="building"
							bind:value={building}
							required
							placeholder="Main"
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>

					<!-- Floor -->
					<div>
						<label for="floor" class="block text-sm font-medium text-gray-700 mb-2">
							Floor *
						</label>
						<input
							type="number"
							id="floor"
							bind:value={floor}
							required
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>

					<!-- Capacity -->
					<div>
						<label for="capacity" class="block text-sm font-medium text-gray-700 mb-2">
							Capacity *
						</label>
						<input
							type="number"
							id="capacity"
							bind:value={capacity}
							required
							min="1"
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>

					<!-- Parent Location (Optional) -->
					<div>
						<label for="parent_location_id" class="block text-sm font-medium text-gray-700 mb-2">
							Parent Location (Optional)
						</label>
						<select
							id="parent_location_id"
							bind:value={parentLocationId}
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						>
							<option value="">None</option>
							{#each availableLocations as location}
								<option value={location.id}>{location.name}</option>
							{/each}
						</select>
					</div>

					<!-- Error Message -->
					{#if errorMessage}
						<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
							{errorMessage}
						</div>
					{/if}

					<!-- Actions -->
					<div class="flex gap-4 justify-end">
						<button
							type="button"
							onclick={handleCancel}
							class="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium"
						>
							Cancel
						</button>
						<button
							type="submit"
							disabled={isSubmitting}
							class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
						>
							{isSubmitting ? 'Saving...' : 'Save Changes'}
						</button>
					</div>
				</div>
			</form>
		</div>
	</main>
</div>
