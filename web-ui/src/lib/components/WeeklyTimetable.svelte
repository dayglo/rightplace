<script lang="ts">
	import type { ScheduleEntry, Location } from '$lib/services/api';
	import { getActivityIcon, getActivityName, getDayName } from '$lib/utils';

	interface Props {
		schedules: ScheduleEntry[];
		locations: Location[];
	}

	let { schedules, locations }: Props = $props();

	let showFullWeek = $state(false);

	const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

	// Get current day of week (0=Monday)
	const currentDay = $derived(() => {
		const today = new Date();
		const dayNum = today.getDay();
		return dayNum === 0 ? 6 : dayNum - 1; // Convert Sunday from 0 to 6
	});

	// Helper to get location name by ID
	function getLocationName(locationId: string): string {
		const location = locations.find(l => l.id === locationId);
		return location ? location.name : 'Unknown';
	}

	// Get schedule entries for a specific day
	function getDaySchedule(dayIndex: number): ScheduleEntry[] {
		return schedules
			.filter(s => s.day_of_week === dayIndex)
			.sort((a, b) => a.start_time.localeCompare(b.start_time));
	}
</script>

<div class="bg-white rounded-lg shadow p-6">
	<div class="flex justify-between items-center mb-4">
		<h2 class="text-xl font-bold">🕐 Weekly Timetable</h2>
		<button
			onclick={() => showFullWeek = !showFullWeek}
			class="text-blue-600 text-sm hover:text-blue-800"
		>
			{showFullWeek ? 'Collapse ▲' : 'Show Full Week ▼'}
		</button>
	</div>

	{#each days as day, index}
		<div class="mb-4 {showFullWeek || index === currentDay() ? '' : 'hidden'}">
			<h3 class="font-bold text-gray-700 mb-2">
				{day}
				{#if index === currentDay()}
					<span class="text-blue-600 text-sm">(Today)</span>
				{/if}
			</h3>

			{#each getDaySchedule(index) as entry (entry.id)}
				<div class="flex items-start ml-4 mb-2">
					<span class="text-gray-500 text-sm w-24 flex-shrink-0">
						{entry.start_time}-{entry.end_time}
					</span>
					<span class="text-xl mr-2">{getActivityIcon(entry.activity_type)}</span>
					<div>
						<span class="font-medium">{getActivityName(entry.activity_type)}</span>
						<span class="text-gray-600 text-sm ml-2">({getLocationName(entry.location_id)})</span>
					</div>
				</div>
			{:else}
				<p class="text-gray-400 text-sm ml-4">No activities scheduled</p>
			{/each}
		</div>
	{/each}
</div>
