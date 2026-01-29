<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';
	import { startCamera, stopCamera, captureFrame } from '$lib/services/camera';
	import { enrollFace } from '$lib/services/api';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	type EnrollmentState = 'initializing' | 'ready' | 'capturing' | 'success' | 'error';

	let videoElement: HTMLVideoElement | null = $state(null);
	let state: EnrollmentState = $state('initializing');
	let statusMessage = $state('Initializing camera...');
	let errorMessage = $state('');
	let qualityGood = $state(false);

	const fullName = $derived(`${data.inmate.first_name} ${data.inmate.last_name}`);

	onMount(async () => {
		if (videoElement) {
			const result = await startCamera(videoElement);
			if (result.success) {
				state = 'ready';
				statusMessage = 'Ready to capture';
				qualityGood = true;
			} else {
				state = 'error';
				statusMessage = 'Camera error';
				errorMessage = result.error || 'Failed to access camera';
			}
		}
	});

	onDestroy(() => {
		stopCamera();
	});

	async function handleCapture() {
		if (!videoElement || state !== 'ready') return;

		state = 'capturing';
		statusMessage = 'Capturing photo...';

		try {
			const imageData = captureFrame(videoElement);
			
			// Upload to backend (enrollFace expects base64 string)
			await enrollFace(data.inmate.id, imageData);

			state = 'success';
			statusMessage = 'Enrollment successful!';

			// Redirect after short delay
			setTimeout(() => {
				goto('/prisoners');
			}, 2000);
		} catch (error) {
			state = 'error';
			statusMessage = 'Enrollment failed';
			errorMessage = error instanceof Error ? error.message : 'Failed to enroll face';
			
			// Allow retry
			setTimeout(() => {
				state = 'ready';
				statusMessage = 'Ready to capture';
				errorMessage = '';
			}, 3000);
		}
	}
</script>

<div class="min-h-screen bg-gray-50">
	<main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Header -->
		<div class="flex items-center justify-between mb-6">
			<div>
				<h1 class="text-3xl font-bold text-gray-900">
					Enroll Face: {fullName}
				</h1>
				<p class="text-gray-600 mt-1">#{data.inmate.inmate_number}</p>
			</div>
			<a
				href="/prisoners"
				class="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-2"
			>
				← Back
			</a>
		</div>

		<!-- Camera Preview -->
		<div class="bg-white rounded-lg shadow p-6">
			<div class="flex flex-col items-center">
				<!-- Video Preview -->
				<div class="relative w-full max-w-2xl aspect-video bg-gray-900 rounded-lg overflow-hidden mb-6">
					<video
						bind:this={videoElement}
						autoplay
						playsinline
						muted
						class="w-full h-full object-cover"
					></video>

					<!-- Face Detection Overlay (placeholder) -->
					{#if state === 'ready' || state === 'capturing'}
						<div
							class="absolute inset-0 flex items-center justify-center pointer-events-none"
						>
							<div
								class="border-4 border-blue-500 rounded-lg"
								style="width: 60%; height: 80%;"
							></div>
						</div>
					{/if}

					<!-- Success Overlay -->
					{#if state === 'success'}
						<div
							class="absolute inset-0 bg-green-500 bg-opacity-20 flex items-center justify-center"
						>
							<div class="bg-white rounded-lg p-6 text-center">
								<div class="text-6xl mb-4">✓</div>
								<p class="text-xl font-semibold text-green-600">Success!</p>
							</div>
						</div>
					{/if}
				</div>

				<!-- Status -->
				<div class="w-full max-w-2xl mb-6">
					<div class="flex items-center justify-between mb-2">
						<p class="text-sm font-medium text-gray-700">
							Status: <span
								class:text-blue-600={state === 'ready'}
								class:text-yellow-600={state === 'initializing' || state === 'capturing'}
								class:text-green-600={state === 'success'}
								class:text-red-600={state === 'error'}
							>
								{statusMessage}
							</span>
						</p>
						{#if qualityGood && state === 'ready'}
							<p class="text-sm font-medium text-green-600">Quality: Good ✓</p>
						{/if}
					</div>

					{#if errorMessage}
						<div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
							{errorMessage}
						</div>
					{/if}
				</div>

				<!-- Capture Button -->
				<button
					onclick={handleCapture}
					disabled={state !== 'ready'}
					class="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-lg disabled:opacity-50 disabled:cursor-not-allowed mb-6"
				>
					{#if state === 'capturing'}
						Capturing...
					{:else if state === 'success'}
						Success!
					{:else}
						Capture Photo
					{/if}
				</button>

				<!-- Instructions -->
				<div class="w-full max-w-2xl bg-blue-50 border border-blue-200 rounded-lg p-6">
					<h3 class="font-semibold text-gray-900 mb-3">Instructions:</h3>
					<ul class="space-y-2 text-sm text-gray-700">
						<li class="flex items-start gap-2">
							<span class="text-blue-600">•</span>
							<span>Position face in center of frame</span>
						</li>
						<li class="flex items-start gap-2">
							<span class="text-blue-600">•</span>
							<span>Ensure good lighting</span>
						</li>
						<li class="flex items-start gap-2">
							<span class="text-blue-600">•</span>
							<span>Look directly at camera</span>
						</li>
						<li class="flex items-start gap-2">
							<span class="text-blue-600">•</span>
							<span>Remove glasses if possible</span>
						</li>
					</ul>
				</div>
			</div>
		</div>
	</main>
</div>
