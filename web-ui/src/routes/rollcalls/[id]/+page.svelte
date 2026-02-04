<script lang="ts">
	import type { PageData } from './$types';
	import { goto } from '$app/navigation';
	import { startRollCall } from '$lib/services/api';
	import type { Verification, Location, Inmate } from '$lib/services/api';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let isStarting = $state(false);
	let error = $state('');

	// Helper to get location name
	function getLocationName(locationId: string): string {
		const location = data.locations.find((loc) => loc.id === locationId);
		return location?.name || locationId;
	}

	// Helper to get inmate details
	function getInmate(inmateId: string): Inmate | undefined {
		return data.inmates.find((inmate) => inmate.id === inmateId);
	}

	// Helper to get verifications for a location
	function getVerificationsForLocation(locationId: string): Verification[] {
		return data.verifications.filter((v) => v.location_id === locationId);
	}

	// Helper to get verification for a specific inmate at a location
	function getVerificationForInmate(inmateId: string, locationId: string): Verification | undefined {
		return data.verifications.find(
			(v) => v.inmate_id === inmateId && v.location_id === locationId
		);
	}

	// Calculate summary statistics
	const stats = $derived(() => {
		const totalLocations = data.rollCall.route.length;
		const totalExpected = data.rollCall.route.reduce(
			(sum, stop) => sum + stop.expected_inmates.length,
			0
		);

		const verified = data.verifications.filter((v) => v.status === 'verified').length;
		const notFound = data.verifications.filter((v) => v.status === 'not_found').length;
		const manual = data.verifications.filter((v) => v.is_manual_override).length;

		const verifiedWithConfidence = data.verifications.filter((v) => v.status === 'verified');
		const avgConfidence =
			verifiedWithConfidence.length > 0
				? verifiedWithConfidence.reduce((sum, v) => sum + v.confidence, 0) /
				  verifiedWithConfidence.length
				: 0;

		return {
			totalLocations,
			totalExpected,
			verified,
			notFound,
			manual,
			avgConfidence: Math.round(avgConfidence * 100)
		};
	});

	// Calculate duration
	const duration = $derived(() => {
		if (!data.rollCall.started_at || !data.rollCall.completed_at) return null;

		const start = new Date(data.rollCall.started_at);
		const end = new Date(data.rollCall.completed_at);
		const diffMs = end.getTime() - start.getTime();
		const diffMins = Math.floor(diffMs / 60000);

		return `${diffMins}m`;
	});

	// Format datetime
	function formatDateTime(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric',
			hour: 'numeric',
			minute: '2-digit',
			hour12: true
		});
	}

	// Format time only
	function formatTime(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleTimeString('en-US', {
			hour: 'numeric',
			minute: '2-digit',
			hour12: true
		});
	}

	// Get status badge color
	function getStatusColor(status: string): string {
		switch (status) {
			case 'scheduled':
				return 'bg-blue-100 text-blue-800';
			case 'in_progress':
				return 'bg-yellow-100 text-yellow-800';
			case 'completed':
				return 'bg-green-100 text-green-800';
			case 'cancelled':
				return 'bg-red-100 text-red-800';
			default:
				return 'bg-gray-100 text-gray-800';
		}
	}

	// Get verification status badge
	function getVerificationBadge(status: string): { color: string; text: string } {
		switch (status) {
			case 'verified':
				return { color: 'bg-green-100 text-green-800', text: '✓ Verified' };
			case 'not_found':
				return { color: 'bg-red-100 text-red-800', text: '✗ Not Found' };
			case 'wrong_location':
				return { color: 'bg-orange-100 text-orange-800', text: '⚠ Wrong Location' };
			case 'manual':
				return { color: 'bg-blue-100 text-blue-800', text: '👤 Manual' };
			case 'pending':
				return { color: 'bg-gray-100 text-gray-800', text: '○ Pending' };
			default:
				return { color: 'bg-gray-100 text-gray-800', text: status };
		}
	}

	// Handle start roll call
	async function handleStartRollCall() {
		if (isStarting) return;

		isStarting = true;
		error = '';

		try {
			await startRollCall(data.rollCall.id);
			goto(`/rollcalls/${data.rollCall.id}/active`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to start roll call';
			isStarting = false;
		}
	}
</script>

<div class="min-h-screen bg-gray-50">
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Header -->
		<div class="mb-6">
			<div class="flex justify-between items-start mb-2">
				<div class="flex-1">
					<h1 class="text-3xl font-bold text-gray-900">{data.rollCall.name}</h1>
					<p class="text-gray-600 mt-1">{formatDateTime(data.rollCall.scheduled_at)}</p>
				</div>
				<a
					href="/rollcalls"
					class="text-gray-600 hover:text-gray-900 font-medium"
				>
					← Back
				</a>
			</div>

			<div class="flex flex-wrap items-center gap-4 mt-4">
				<!-- Status Badge -->
				<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium {getStatusColor(data.rollCall.status)}">
					{data.rollCall.status.charAt(0).toUpperCase() + data.rollCall.status.slice(1).replace('_', ' ')}
				</span>

				<!-- Time Information -->
				{#if data.rollCall.started_at}
					<span class="text-sm text-gray-600">
						Started: {formatTime(data.rollCall.started_at)}
					</span>
				{/if}

				{#if data.rollCall.completed_at}
					<span class="text-sm text-gray-600">
						Completed: {formatTime(data.rollCall.completed_at)}
					</span>
				{/if}

				{#if duration()}
					<span class="text-sm text-gray-600">
						Duration: {duration()}
					</span>
				{/if}
			</div>

			<!-- Officer Info -->
			{#if data.rollCall.officer_id}
				<p class="text-sm text-gray-600 mt-2">
					Officer: {data.rollCall.officer_id}
				</p>
			{/if}

			<!-- Notes -->
			{#if data.rollCall.notes}
				<p class="text-sm text-gray-600 mt-2">
					Notes: {data.rollCall.notes}
				</p>
			{/if}
		</div>

		<!-- Summary Card (if in-progress or completed) -->
		{#if data.rollCall.status === 'in_progress' || data.rollCall.status === 'completed'}
			<div class="bg-white rounded-lg shadow p-6 mb-6">
				<h2 class="text-xl font-semibold text-gray-900 mb-4">Summary</h2>

				<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
					<div class="bg-blue-50 rounded-lg p-4">
						<div class="text-2xl font-bold text-blue-900">{stats().totalLocations}</div>
						<div class="text-sm text-blue-700">Total Locations</div>
					</div>

					<div class="bg-green-50 rounded-lg p-4">
						<div class="text-2xl font-bold text-green-900">{stats().totalExpected}</div>
						<div class="text-sm text-green-700">Total Prisoners</div>
					</div>

					<div class="bg-purple-50 rounded-lg p-4">
						<div class="text-2xl font-bold text-purple-900">{stats().verified}</div>
						<div class="text-sm text-purple-700">Verified</div>
					</div>

					<div class="bg-orange-50 rounded-lg p-4">
						<div class="text-2xl font-bold text-orange-900">{stats().avgConfidence}%</div>
						<div class="text-sm text-orange-700">Avg Confidence</div>
					</div>
				</div>

				<div class="mt-4 flex flex-wrap gap-4 text-sm">
					<span class="text-gray-700">
						Not Found: <span class="font-semibold">{stats().notFound}</span>
					</span>
					<span class="text-gray-700">
						Manual Override: <span class="font-semibold">{stats().manual}</span>
					</span>
				</div>
			</div>
		{/if}

		<!-- Route Details -->
		<div class="bg-white rounded-lg shadow p-6 mb-6">
			<h2 class="text-xl font-semibold text-gray-900 mb-4">Route Details</h2>

			<div class="space-y-4">
				{#each data.rollCall.route as stop, index (stop.id)}
					{@const locationName = getLocationName(stop.location_id)}
					{@const verificationsAtLocation = getVerificationsForLocation(stop.location_id)}

					<div class="border border-gray-300 rounded-lg p-4">
						<!-- Location Header -->
						<div class="flex items-center justify-between mb-3">
							<div class="flex items-center gap-3">
								<div class="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-semibold">
									{stop.order}
								</div>
								<div>
									<h3 class="font-semibold text-gray-900">{locationName}</h3>
									{#if stop.arrived_at || stop.completed_at}
										<p class="text-xs text-gray-600">
											{#if stop.arrived_at}Arrived: {formatTime(stop.arrived_at)}{/if}
											{#if stop.completed_at} | Completed: {formatTime(stop.completed_at)}{/if}
										</p>
									{/if}
								</div>
							</div>

							<!-- Stop Status Badge -->
							<span class="text-xs px-2 py-1 rounded-full {stop.status === 'completed' ? 'bg-green-100 text-green-800' : stop.status === 'current' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'}">
								{stop.status}
							</span>
						</div>

						<!-- Expected Prisoners -->
						<div class="ml-11 space-y-2">
							{#if stop.expected_inmates.length === 0}
								<p class="text-sm text-gray-500 italic">No prisoners expected at this location</p>
							{:else}
								{#each stop.expected_inmates as inmateId (inmateId)}
									{@const inmate = getInmate(inmateId)}
									{@const verification = getVerificationForInmate(inmateId, stop.location_id)}

									{#if inmate}
										<div class="flex items-start justify-between p-3 bg-gray-50 rounded">
											<div class="flex-1">
												<div class="font-medium text-gray-900">
													{inmate.first_name} {inmate.last_name}
													<span class="text-gray-600 font-normal text-sm">
														(#{inmate.inmate_number})
													</span>
												</div>

												{#if verification}
													<div class="mt-1 flex items-center gap-3 text-xs">
														<span class="{getVerificationBadge(verification.status).color} px-2 py-1 rounded-full">
															{getVerificationBadge(verification.status).text}
														</span>
														{#if verification.status === 'verified'}
															<span class="text-gray-600">
																Confidence: {Math.round(verification.confidence * 100)}%
															</span>
														{/if}
														<span class="text-gray-600">
															{formatTime(verification.timestamp)}
														</span>
														{#if verification.is_manual_override}
															<span class="text-orange-600 font-medium">Manual Override</span>
														{/if}
													</div>

													{#if verification.notes}
														<p class="mt-1 text-xs text-gray-600">{verification.notes}</p>
													{/if}
												{:else if data.rollCall.status !== 'scheduled'}
													<div class="mt-1 text-xs text-gray-500">Pending verification</div>
												{/if}
											</div>
										</div>
									{/if}
								{/each}
							{/if}
						</div>
					</div>
				{/each}
			</div>
		</div>

		<!-- Error Message -->
		{#if error}
			<div class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
				{error}
			</div>
		{/if}

		<!-- Action Buttons -->
		<div class="flex flex-wrap gap-4">
			{#if data.rollCall.status === 'scheduled'}
				<button
					onclick={handleStartRollCall}
					disabled={isStarting}
					class="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{isStarting ? 'Starting...' : 'Start Roll Call'}
				</button>
			{/if}

			{#if data.rollCall.status === 'in_progress'}
				<a
					href="/rollcalls/{data.rollCall.id}/active"
					class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium inline-block"
				>
					View Active Roll Call
				</a>
			{/if}

			<!-- Visualization Link (available for all statuses) -->
			<a
				href="/rollcalls/visualization?rollcall_id={data.rollCall.id}"
				class="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium inline-block"
			>
				📊 View Visualization
			</a>

			{#if data.rollCall.status === 'completed'}
				<button
					disabled
					class="px-4 py-2 border border-gray-300 rounded-lg text-gray-400 cursor-not-allowed"
				>
					Export PDF (Coming Soon)
				</button>
				<button
					disabled
					class="px-4 py-2 border border-gray-300 rounded-lg text-gray-400 cursor-not-allowed"
				>
					Export CSV (Coming Soon)
				</button>
			{/if}
		</div>
	</main>
</div>
