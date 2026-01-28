<script lang="ts">
	import type { PageData } from './$types';
	import PrisonerCard from '$lib/components/PrisonerCard.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let searchTerm = $state('');
	let filterStatus = $state<'all' | 'enrolled' | 'not_enrolled'>('all');

	const filteredInmates = $derived(() => {
		let result = data.inmates;

		// Filter by search term
		if (searchTerm) {
			const search = searchTerm.toLowerCase();
			result = result.filter(
				(inmate) =>
					inmate.first_name.toLowerCase().includes(search) ||
					inmate.last_name.toLowerCase().includes(search) ||
					inmate.inmate_number.toLowerCase().includes(search)
			);
		}

		// Filter by enrollment status
		if (filterStatus === 'enrolled') {
			result = result.filter((inmate) => inmate.is_enrolled);
		} else if (filterStatus === 'not_enrolled') {
			result = result.filter((inmate) => !inmate.is_enrolled);
		}

		return result;
	});

	const enrolledCount = $derived(data.inmates.filter((i) => i.is_enrolled).length);
	const notEnrolledCount = $derived(data.inmates.filter((i) => !i.is_enrolled).length);
</script>

<div class="min-h-screen bg-gray-50">
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Header -->
		<div class="flex justify-between items-center mb-6">
			<h1 class="text-3xl font-bold text-gray-900">Prisoners</h1>
			<a
				href="/prisoners/new"
				class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium"
			>
				+ Add Prisoner
			</a>
		</div>

		<!-- Search and Filter -->
		<div class="bg-white rounded-lg shadow p-6 mb-6">
			<div class="flex flex-col sm:flex-row gap-4">
				<input
					type="text"
					bind:value={searchTerm}
					placeholder="Search by name or number..."
					class="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
				/>
				<select
					bind:value={filterStatus}
					class="border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
				>
					<option value="all">All</option>
					<option value="enrolled">Enrolled</option>
					<option value="not_enrolled">Not Enrolled</option>
				</select>
			</div>

			<!-- Stats -->
			<div class="mt-4 flex gap-6 text-sm text-gray-600">
				<span>Total: {data.inmates.length}</span>
				<span>Enrolled: {enrolledCount}</span>
				<span>Not Enrolled: {notEnrolledCount}</span>
			</div>
		</div>

		<!-- Prisoner List -->
		{#if filteredInmates().length === 0}
			<div class="bg-white rounded-lg shadow p-12 text-center">
				<p class="text-gray-500 text-lg">No prisoners found</p>
			</div>
		{:else}
			<div class="space-y-4">
				{#each filteredInmates() as inmate (inmate.id)}
					<PrisonerCard {inmate} />
				{/each}
			</div>
		{/if}
	</main>
</div>
