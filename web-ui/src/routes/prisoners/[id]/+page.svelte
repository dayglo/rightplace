<script lang="ts">
	import type { PageData } from './$types';
	import type { ScheduleEntry } from '$lib/services/api';
	import NowAndNext from '$lib/components/NowAndNext.svelte';
	import WeeklyTimetable from '$lib/components/WeeklyTimetable.svelte';
	import LocationHistory from '$lib/components/LocationHistory.svelte';
	import { formatDate, calculateAge } from '$lib/utils';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	const latestVerification = $derived(
		data.verifications.length > 0 ? data.verifications[0] : null
	);

	const nextSchedule = $derived(() => {
		const now = new Date();
		const dayOfWeek = now.getDay() === 0 ? 6 : now.getDay() - 1; // Convert to 0=Mon
		const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;

		// Find next activity today
		const todaySchedules = data.schedules
			.filter((s: ScheduleEntry) => s.day_of_week === dayOfWeek && s.start_time > currentTime)
			.sort((a: ScheduleEntry, b: ScheduleEntry) => a.start_time.localeCompare(b.start_time));

		if (todaySchedules.length > 0) {
			return todaySchedules[0];
		}

		// Check tomorrow
		const tomorrowDay = (dayOfWeek + 1) % 7;
		const tomorrowSchedules = data.schedules
			.filter((s: ScheduleEntry) => s.day_of_week === tomorrowDay)
			.sort((a: ScheduleEntry, b: ScheduleEntry) => a.start_time.localeCompare(b.start_time));

		return tomorrowSchedules.length > 0 ? tomorrowSchedules[0] : null;
	});

	// Helper to get location name
	function getHomeLocation(): string {
		if (!data.inmate.cell_block || !data.inmate.cell_number) {
			return 'Not assigned';
		}
		return `${data.inmate.cell_block}-${data.inmate.cell_number}`;
	}
</script>

<div class="min-h-screen bg-gray-50">
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Header -->
		<div class="flex justify-between items-start mb-6">
			<div>
				<a href="/prisoners" class="text-blue-600 hover:text-blue-800 mb-2 inline-block">
					← Back to Prisoners
				</a>
				<div class="flex items-center gap-4">
					<h1 class="text-3xl font-bold text-gray-900">
						{data.inmate.first_name} {data.inmate.last_name}
					</h1>
					{#if data.inmate.is_enrolled}
						<span class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
							✓ Enrolled
						</span>
					{:else}
						<span class="bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-sm">
							Not Enrolled
						</span>
					{/if}
				</div>
				<p class="text-gray-600 mt-1">#{data.inmate.inmate_number}</p>
			</div>
			<div class="flex gap-2">
				<!-- Future enhancement: Edit and Re-enroll buttons -->
				<!-- <a
					href="/prisoners/{data.inmate.id}/edit"
					class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
				>
					Edit
				</a>
				<a
					href="/prisoners/{data.inmate.id}/enroll"
					class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
				>
					Re-enroll Face
				</a> -->
			</div>
		</div>

		<!-- Prisoner Info Card -->
		<div class="bg-white rounded-lg shadow p-6 mb-6">
			<div class="flex gap-6">
				<!-- Photo -->
				<div class="w-32 h-32 bg-gray-200 rounded-lg flex items-center justify-center flex-shrink-0">
					{#if data.inmate.photo_uri}
						<img
							src={data.inmate.photo_uri}
							alt="Prisoner photo"
							class="w-full h-full object-cover rounded-lg"
						/>
					{:else}
						<span class="text-gray-400 text-4xl">👤</span>
					{/if}
				</div>

				<!-- Details -->
				<div class="flex-1">
					<div class="grid grid-cols-2 gap-4">
						<div>
							<div class="text-sm text-gray-500">Prisoner Number</div>
							<div class="font-medium">{data.inmate.inmate_number}</div>
						</div>
						<div>
							<div class="text-sm text-gray-500">Date of Birth</div>
							<div class="font-medium">
								{formatDate(data.inmate.date_of_birth)}
								({calculateAge(data.inmate.date_of_birth)} years)
							</div>
						</div>
						<div>
							<div class="text-sm text-gray-500">Home Location</div>
							<div class="font-medium">{getHomeLocation()}</div>
						</div>
						<div>
							<div class="text-sm text-gray-500">Enrollment Status</div>
							<div class="font-medium">
								{#if data.inmate.is_enrolled}
									Enrolled
									{#if data.inmate.enrolled_at}
										on {formatDate(data.inmate.enrolled_at)}
									{/if}
								{:else}
									Not Enrolled
								{/if}
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Now & Next -->
		<div class="mb-6">
			<NowAndNext
				latestVerification={latestVerification}
				nextSchedule={nextSchedule()}
				currentTime={new Date()}
				locations={data.locations}
			/>
		</div>

		<!-- Weekly Timetable -->
		<div class="mb-6">
			<WeeklyTimetable schedules={data.schedules} locations={data.locations} />
		</div>

		<!-- Location History -->
		<div>
			<LocationHistory
				verifications={data.verifications}
				locations={data.locations}
				limit={7}
				inmateId={data.inmate.id}
			/>
		</div>
	</main>
</div>
