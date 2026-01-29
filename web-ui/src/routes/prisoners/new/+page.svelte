<script lang="ts">
	import { goto } from '$app/navigation';
	import { createInmate } from '$lib/services/api';

	let inmateNumber = $state('');
	let firstName = $state('');
	let lastName = $state('');
	let dateOfBirth = $state('');
	let cellBlock = $state('A');
	let cellNumber = $state('');
	let isSubmitting = $state(false);
	let errorMessage = $state('');

	const cellBlocks = ['A', 'B', 'C', 'D', 'E'];

	async function handleSubmit(event: Event) {
		event.preventDefault();
		isSubmitting = true;
		errorMessage = '';

		try {
			const inmate = await createInmate({
				inmate_number: inmateNumber,
				first_name: firstName,
				last_name: lastName,
				date_of_birth: dateOfBirth,
				cell_block: cellBlock,
				cell_number: cellNumber
			});

			// Redirect to enrollment page
			goto(`/prisoners/${inmate.id}/enroll`);
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Failed to create prisoner';
			isSubmitting = false;
		}
	}

	function handleCancel() {
		goto('/prisoners');
	}
</script>

<div class="min-h-screen bg-gray-50">
	<main class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Header -->
		<div class="flex items-center justify-between mb-6">
			<h1 class="text-3xl font-bold text-gray-900">Add New Prisoner</h1>
			<a
				href="/prisoners"
				class="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-2"
			>
				← Back
			</a>
		</div>

		<!-- Form -->
		<div class="bg-white rounded-lg shadow p-6">
			<form onsubmit={handleSubmit}>
				<div class="space-y-6">
					<!-- Inmate Number -->
					<div>
						<label for="inmate_number" class="block text-sm font-medium text-gray-700 mb-2">
							Inmate Number *
						</label>
						<input
							type="text"
							id="inmate_number"
							bind:value={inmateNumber}
							required
							placeholder="A12345"
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>

					<!-- First Name -->
					<div>
						<label for="first_name" class="block text-sm font-medium text-gray-700 mb-2">
							First Name *
						</label>
						<input
							type="text"
							id="first_name"
							bind:value={firstName}
							required
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>

					<!-- Last Name -->
					<div>
						<label for="last_name" class="block text-sm font-medium text-gray-700 mb-2">
							Last Name *
						</label>
						<input
							type="text"
							id="last_name"
							bind:value={lastName}
							required
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>

					<!-- Date of Birth -->
					<div>
						<label for="date_of_birth" class="block text-sm font-medium text-gray-700 mb-2">
							Date of Birth *
						</label>
						<input
							type="date"
							id="date_of_birth"
							bind:value={dateOfBirth}
							required
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>

					<!-- Cell Block -->
					<div>
						<label for="cell_block" class="block text-sm font-medium text-gray-700 mb-2">
							Cell Block *
						</label>
						<select
							id="cell_block"
							bind:value={cellBlock}
							required
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						>
							{#each cellBlocks as block}
								<option value={block}>{block}</option>
							{/each}
						</select>
					</div>

					<!-- Cell Number -->
					<div>
						<label for="cell_number" class="block text-sm font-medium text-gray-700 mb-2">
							Cell Number *
						</label>
						<input
							type="text"
							id="cell_number"
							bind:value={cellNumber}
							required
							placeholder="101"
							class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
					</div>

					<!-- Error Message -->
					{#if errorMessage}
						<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
							{errorMessage}
						</div>
					{/if}

					<!-- Actions -->
					<div class="flex gap-4 justify-end">
						<button
							type="button"
							onclick={handleCancel}
							class="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium"
						>
							Cancel
						</button>
						<button
							type="submit"
							disabled={isSubmitting}
							class="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
						>
							{isSubmitting ? 'Creating...' : 'Create Prisoner'}
						</button>
					</div>
				</div>
			</form>
		</div>
	</main>
</div>
