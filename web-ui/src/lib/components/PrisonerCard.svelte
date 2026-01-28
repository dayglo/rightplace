<script lang="ts">
	import type { Inmate } from '$lib/services/api';

	interface Props {
		inmate: Inmate;
	}

	let { inmate }: Props = $props();

	const fullName = $derived(`${inmate.first_name} ${inmate.last_name}`);
	const cellLocation = $derived(`Block ${inmate.cell_block}, Cell ${inmate.cell_number}`);
</script>

<div class="bg-white rounded-lg shadow p-6 flex items-start gap-4">
	<!-- Photo/Placeholder -->
	<div class="flex-shrink-0">
		{#if inmate.is_enrolled}
			<div
				class="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center text-2xl text-blue-600"
			>
				👤
			</div>
		{:else}
			<div
				class="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center text-2xl text-gray-400"
			>
				?
			</div>
		{/if}
	</div>

	<!-- Info -->
	<div class="flex-1">
		<div class="flex items-start justify-between">
			<div>
				<h3 class="text-lg font-semibold text-gray-900">{fullName}</h3>
				<p class="text-sm text-gray-600">#{inmate.inmate_number} | {cellLocation}</p>
				<p class="text-sm text-gray-500 mt-1">
					{#if inmate.is_enrolled}
						Enrolled: {new Date(inmate.updated_at).toLocaleDateString()}
					{:else}
						Not enrolled
					{/if}
				</p>
			</div>

			<!-- Status Icon -->
			<div class="flex-shrink-0">
				{#if inmate.is_enrolled}
					<span class="text-2xl text-green-600">✓</span>
				{:else}
					<span class="text-2xl text-red-600">✗</span>
				{/if}
			</div>
		</div>

		<!-- Actions -->
		<div class="mt-4 flex gap-2">
			<a
				href="/prisoners/{inmate.id}"
				class="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 border border-blue-600 rounded-lg hover:bg-blue-50"
			>
				View
			</a>
			<a
				href="/prisoners/{inmate.id}/enroll"
				class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg"
			>
				Enroll Face
			</a>
		</div>
	</div>
</div>
