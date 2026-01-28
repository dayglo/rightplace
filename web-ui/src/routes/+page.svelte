<script lang="ts">
	import Navigation from '$lib/components/Navigation.svelte';
	import StatCard from '$lib/components/StatCard.svelte';
	import RollCallCard from '$lib/components/RollCallCard.svelte';
	import type { Inmate, Location, RollCall } from '$lib/services/api';

	interface Props {
		data: {
			inmates: Inmate[];
			locations: Location[];
			rollCalls: RollCall[];
		};
	}

	let { data }: Props = $props();

	// Count enrolled inmates - use derived state
	let enrolledCount = $derived(data.inmates.filter((inmate) => inmate.is_enrolled).length);

	// Get recent roll calls (limit to 5) - use derived state
	let recentRollCalls = $derived(data.rollCalls.slice(0, 5));

	// Calculate verification counts for roll calls
	// For now, we'll use placeholder logic - in real app would fetch from verification records
	function getVerificationCounts(rollCall: RollCall) {
		// Count expected inmates from route
		const totalCount = rollCall.route.reduce(
			(sum, stop) => sum + stop.expected_inmate_ids.length,
			0
		);

		// For completed roll calls, assume all verified
		// For in_progress, assume partial verification
		const verifiedCount =
			rollCall.status === 'completed'
				? totalCount
				: rollCall.status === 'in_progress'
					? Math.floor(totalCount / 2)
					: 0;

		return { verifiedCount, totalCount };
	}
</script>

<div class="min-h-screen bg-gray-50">
	<Navigation />

	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Stats Grid -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
			<StatCard
				title="Prisoners"
				count={enrolledCount}
				suffix="enrolled"
				href="/prisoners"
				icon="👤"
			/>
			<StatCard
				title="Locations"
				count={data.locations.length}
				suffix="total"
				href="/locations"
				icon="🏢"
			/>
		</div>

		<!-- Recent Roll Calls -->
		<div class="bg-white rounded-lg shadow p-6 mb-8">
			<h2 class="text-2xl font-bold text-gray-900 mb-4">Recent Roll Calls</h2>
			{#if recentRollCalls.length > 0}
				<div class="space-y-3">
					{#each recentRollCalls as rollCall}
						{@const { verifiedCount, totalCount } = getVerificationCounts(rollCall)}
						<RollCallCard {rollCall} {verifiedCount} {totalCount} />
					{/each}
				</div>
			{:else}
				<p class="text-gray-500 text-center py-8">No recent roll calls</p>
			{/if}
		</div>

		<!-- Quick Actions -->
		<div class="bg-white rounded-lg shadow p-6">
			<h2 class="text-2xl font-bold text-gray-900 mb-4">Quick Actions</h2>
			<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
				<a
					href="/prisoners/new"
					class="flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-6 rounded-lg transition-colors"
				>
					+ New Prisoner
				</a>
				<a
					href="/locations/new"
					class="flex items-center justify-center bg-green-600 hover:bg-green-700 text-white font-semibold py-4 px-6 rounded-lg transition-colors"
				>
					+ New Location
				</a>
				<a
					href="/rollcalls/new"
					class="flex items-center justify-center bg-purple-600 hover:bg-purple-700 text-white font-semibold py-4 px-6 rounded-lg transition-colors"
				>
					+ Create Roll Call
				</a>
				<a
					href="/rollcalls"
					class="flex items-center justify-center bg-gray-600 hover:bg-gray-700 text-white font-semibold py-4 px-6 rounded-lg transition-colors"
				>
					View Reports
				</a>
			</div>
		</div>
	</main>
</div>
