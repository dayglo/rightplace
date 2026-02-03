<script lang="ts">
	import type { Location } from '$lib/services/api';

	interface Props {
		location: Location;
		hierarchyPath: string;
		onEdit?: () => void;
		onDelete?: () => void;
	}

	let { location, hierarchyPath, onEdit, onDelete }: Props = $props();

	const getLocationIcon = (type: string): string => {
		switch (type.toLowerCase()) {
			// Hierarchical accommodation
			case 'houseblock':
				return '🏢';
			case 'wing':
				return '🏛️';
			case 'landing':
				return '🪜';
			case 'cell':
				return '🚪';
			// Special units
			case 'healthcare':
				return '🏥';
			case 'segregation':
				return '🔒';
			case 'vpu':
				return '🛡️';
			case 'induction':
				return '📋';
			// Facilities
			case 'education':
				return '📚';
			case 'workshop':
				return '🔧';
			case 'gym':
				return '💪';
			case 'chapel':
				return '⛪';
			case 'visits':
				return '👥';
			case 'reception':
				return '🎫';
			case 'kitchen':
				return '🍳';
			case 'yard':
				return '🌳';
			case 'admin':
				return '🏛️';
			default:
				return '📍';
		}
	};

	const icon = $derived(getLocationIcon(location.type));
</script>

<div class="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
	<div class="flex items-start justify-between">
		<div class="flex items-start gap-4 flex-1">
			<!-- Icon -->
			<div class="text-4xl">{icon}</div>

			<!-- Location Info -->
			<div class="flex-1">
				<h3 class="text-lg font-semibold text-gray-900 mb-2">{hierarchyPath}</h3>
				<div class="text-sm text-gray-600 space-y-1">
					<p>Building: {location.building} | Floor: {location.floor} | Capacity: {location.capacity}</p>
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
