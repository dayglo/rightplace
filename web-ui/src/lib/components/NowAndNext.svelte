<script lang="ts">
	import type { Verification, ScheduleEntry, Location } from '$lib/services/api';
	import { timeAgo, getActivityIcon, getActivityName } from '$lib/utils';

	interface Props {
		latestVerification: Verification | null;
		nextSchedule: ScheduleEntry | null;
		currentTime: Date;
		locations: Location[];
	}

	let { latestVerification, nextSchedule, currentTime, locations }: Props = $props();

	// Helper to get location name by ID
	function getLocationName(locationId: string): string {
		const location = locations.find(l => l.id === locationId);
		return location ? location.name : 'Unknown';
	}

	// Calculate minutes until next activity
	const minutesUntil = $derived(() => {
		if (!nextSchedule) return 0;

		const [hours, minutes] = nextSchedule.start_time.split(':').map(Number);
		const nextTime = new Date(currentTime);
		nextTime.setHours(hours, minutes, 0, 0);

		const diffMs = nextTime.getTime() - currentTime.getTime();
		return Math.floor(diffMs / 60000);
	});

	const isUrgent = $derived(minutesUntil() > 0 && minutesUntil() < 30);
</script>

<div class="bg-white rounded-lg shadow p-6">
	<h2 class="text-xl font-bold mb-4">📍 Now & Next</h2>

	<!-- Current Location -->
	<div class="mb-4">
		<h3 class="text-sm font-medium text-gray-500">Current Location</h3>
		{#if latestVerification}
			<div class="flex items-center mt-2">
				<span class="text-green-500 mr-2">✓</span>
				<span class="font-medium">{getLocationName(latestVerification.location_id)}</span>
				<span class="text-gray-500 ml-2 text-sm">
					• Verified {timeAgo(latestVerification.timestamp)}
				</span>
			</div>
			<div class="text-sm text-gray-600 mt-1">
				{#if latestVerification.confidence > 0}
					Confidence: {Math.round(latestVerification.confidence * 100)}%
				{/if}
				{#if latestVerification.is_manual_override}
					• <span class="text-orange-600">Manual Override</span>
				{/if}
			</div>
		{:else}
			<p class="text-gray-400 mt-2">No recent verification</p>
		{/if}
	</div>

	<!-- Next Activity -->
	<div class="border-t pt-4">
		<h3 class="text-sm font-medium text-gray-500">Next Scheduled Activity</h3>
		{#if nextSchedule}
			<div class="mt-2">
				{#if isUrgent}
					<span class="inline-block bg-orange-100 text-orange-800 text-xs px-2 py-1 rounded mb-2">
						⚠️ Upcoming in {minutesUntil()} minutes
					</span>
				{/if}
				<div class="flex items-center">
					<span class="text-2xl mr-2">{getActivityIcon(nextSchedule.activity_type)}</span>
					<div>
						<div class="font-medium">
							{getActivityName(nextSchedule.activity_type)}
							<span class="text-gray-600">({nextSchedule.start_time}-{nextSchedule.end_time})</span>
						</div>
						<div class="text-sm text-gray-600">{getLocationName(nextSchedule.location_id)}</div>
					</div>
				</div>
			</div>
		{:else}
			<p class="text-gray-400 mt-2">No upcoming activities today</p>
		{/if}
	</div>
</div>
