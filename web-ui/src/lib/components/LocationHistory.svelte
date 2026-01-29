<script lang="ts">
	import type { Verification, Location } from '$lib/services/api';
	import { formatDate, formatTime } from '$lib/utils';

	interface Props {
		verifications: Verification[];
		locations: Location[];
		limit?: number;
		inmateId: string;
	}

	let { verifications, locations, limit = 7, inmateId }: Props = $props();

	// Helper to get location name by ID
	function getLocationName(locationId: string): string {
		const location = locations.find(l => l.id === locationId);
		return location ? location.name : 'Unknown';
	}

	// Get border color based on verification status
	function getBorderColor(verification: Verification): string {
		switch (verification.status) {
			case 'verified':
				return 'border-green-500';
			case 'wrong_location':
				return 'border-orange-500';
			case 'manual':
				return 'border-blue-500';
			default:
				return 'border-red-500';
		}
	}
</script>

<div class="bg-white rounded-lg shadow p-6">
	<div class="flex justify-between items-center mb-4">
		<h2 class="text-xl font-bold">📜 Location History (Last 7 Days)</h2>
		<!-- Future enhancement: link to full history page -->
		<!-- <a href="/prisoners/{inmateId}/history" class="text-blue-600 text-sm hover:text-blue-800">
			View All →
		</a> -->
	</div>

	{#if verifications.length === 0}
		<p class="text-gray-400 text-center py-8">No verification history available</p>
	{:else}
		<div class="space-y-4">
			{#each verifications.slice(0, limit) as verification (verification.id)}
				<div class="border-l-2 pl-4 {getBorderColor(verification)}">
					<!-- Timestamp -->
					<div class="text-sm text-gray-500 mb-1">
						{formatDate(verification.timestamp)} • {formatTime(verification.timestamp)}
					</div>

					<!-- Location -->
					<div class="flex items-center mb-1">
						{#if verification.status === 'verified'}
							<span class="text-green-500 mr-2">✓</span>
						{:else if verification.status === 'wrong_location'}
							<span class="text-orange-500 mr-2">⚠️</span>
						{:else if verification.status === 'manual'}
							<span class="text-blue-500 mr-2">✋</span>
						{:else}
							<span class="text-red-500 mr-2">✗</span>
						{/if}
						<span class="font-medium">{getLocationName(verification.location_id)}</span>
					</div>

					<!-- Details -->
					<div class="text-sm text-gray-600">
						{#if verification.confidence > 0}
							Confidence: {Math.round(verification.confidence * 100)}%
						{/if}
						{#if verification.is_manual_override}
							{#if verification.confidence > 0} • {:else}{/if}
							<span class="text-blue-600">Manual Override</span>
							{#if verification.manual_override_reason}
								({verification.manual_override_reason.replace('_', ' ')})
							{/if}
						{/if}
					</div>

					<!-- Notes -->
					{#if verification.notes}
						<div class="text-sm text-gray-600 mt-1 italic">
							Note: {verification.notes}
						</div>
					{/if}

					<!-- Anomaly Warning -->
					{#if verification.status === 'wrong_location'}
						<div class="bg-orange-50 border border-orange-200 rounded px-3 py-2 mt-2 text-sm">
							<span class="text-orange-800 font-medium">Wrong Location!</span>
							<span class="text-orange-700"> Prisoner was not expected at this location</span>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
