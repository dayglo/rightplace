<script lang="ts">
	import type { Location } from '$lib/services/api';

	interface Props {
		location: Location;
		parentName?: string;
		onEdit?: () => void;
		onDelete?: () => void;
	}

	let { location, parentName, onEdit, onDelete }: Props = $props();

	const getLocationIcon = (type: string): string => {
		switch (type.toLowerCase()) {
			case 'block':
				return '🏢';
			case 'cell':
				return '🚪';
			case 'yard':
				return '🌳';
			default:
				return '📍';
		}
	};

	const icon = $derived(getLocationIcon(location.location_type));
</script>

<div class="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
	<div class="flex items-start justify-between">
		<div class="flex items-start gap-4 flex-1">
			<!-- Icon -->
			<div class="text-4xl">{icon}</div>

			<!-- Location Info -->
			<div class="flex-1">
				<h3 class="text-lg font-semibold text-gray-900 mb-2">{location.name}</h3>
				<div class="text-sm text-gray-600 space-y-1">
					<p>Building: {location.building} | Floor: {location.floor} | Capacity: {location.capacity}</p>
					{#if parentName}
						<p>Parent: {parentName}</p>
					{/if}
				</div>
			</div>
		</div>

		<!-- Actions -->
		<div class="flex gap-2">
			<button
				onclick={onEdit}
				class="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-lg font-medium"
			>
				Edit
			</button>
			<button
				onclick={onDelete}
				class="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded-lg font-medium"
			>
				Delete
			</button>
		</div>
	</div>
</div>
