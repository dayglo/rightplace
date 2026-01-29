<script lang="ts">
	import type { PageData } from './$types';
	import RollCallCard from '$lib/components/RollCallCard.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let filterStatus = $state<string>('all');

	// Filter roll calls by status
	const filteredRollCalls = $derived(() => {
		let result = data.rollcalls;

		if (filterStatus !== 'all') {
			result = result.filter((rc) => rc.status === filterStatus);
		}

		return result;
	});

	// Count roll calls by status
	const scheduledCount = $derived(data.rollcalls.filter((rc) => rc.status === 'scheduled').length);
	const inProgressCount = $derived(data.rollcalls.filter((rc) => rc.status === 'in_progress').length);
	const completedCount = $derived(data.rollcalls.filter((rc) => rc.status === 'completed').length);
	const cancelledCount = $derived(data.rollcalls.filter((rc) => rc.status === 'cancelled').length);

	function formatStatus(status: string): string {
		switch (status) {
			case 'scheduled':
				return 'Scheduled';
			case 'in_progress':
				return 'In Progress';
			case 'completed':
				return 'Completed';
			case 'cancelled':
				return 'Cancelled';
			default:
				return status;
		}
	}
</script>

<div class="min-h-screen bg-gray-50">
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Header -->
		<div class="flex justify-between items-center mb-6">
			<h1 class="text-3xl font-bold text-gray-900">Roll Calls</h1>
			<a
				href="/rollcalls/new"
				class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
			>
				+ Create Roll Call
			</a>
		</div>

		<!-- Filters -->
		<div class="bg-white rounded-lg shadow p-6 mb-6">
			<div class="flex flex-col sm:flex-row gap-4">
				<select
					bind:value={filterStatus}
					class="border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<option value="all">All Statuses</option>
					<option value="scheduled">Scheduled</option>
					<option value="in_progress">In Progress</option>
					<option value="completed">Completed</option>
					<option value="cancelled">Cancelled</option>
				</select>
			</div>

			<!-- Stats -->
			<div class="mt-4 flex gap-6 text-sm text-gray-600">
				<span>Total: {data.rollcalls.length}</span>
				<span>Scheduled: {scheduledCount}</span>
				<span>In Progress: {inProgressCount}</span>
				<span>Completed: {completedCount}</span>
				{#if cancelledCount > 0}
					<span>Cancelled: {cancelledCount}</span>
				{/if}
			</div>
		</div>

		<!-- Roll Call List -->
		{#if filteredRollCalls().length === 0}
			<div class="bg-white rounded-lg shadow p-12 text-center">
				<p class="text-gray-500 text-lg">
					{filterStatus === 'all' ? 'No roll calls found' : `No ${formatStatus(filterStatus).toLowerCase()} roll calls`}
				</p>
				{#if filterStatus === 'all' && data.rollcalls.length === 0}
					<a
						href="/rollcalls/new"
						class="mt-4 inline-block text-blue-600 hover:text-blue-700 font-medium"
					>
						Create your first roll call
					</a>
				{/if}
			</div>
		{:else}
			<div class="space-y-4">
				{#each filteredRollCalls() as rollcall (rollcall.id)}
					<a href="/rollcalls/{rollcall.id}" class="block">
						<RollCallCard
							rollCall={{
								id: rollcall.id,
								name: rollcall.name,
								status: rollcall.status,
								scheduled_time: rollcall.scheduled_at,
								officer_id: rollcall.officer_id,
								route: [],
								notes: rollcall.notes
							}}
							verifiedCount={rollcall.verified_inmates}
							totalCount={rollcall.expected_inmates}
						/>
					</a>
				{/each}
			</div>
		{/if}
	</main>
</div>
