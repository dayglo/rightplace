<script lang="ts">
	import type { PageData } from './$types';
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { verifyFace, completeRollCall } from '$lib/services/api';
	import type { Location, Inmate, RouteStop } from '$lib/services/api';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// Video and canvas refs
	let videoElement: HTMLVideoElement;
	let canvasElement: HTMLCanvasElement;
	let stream: MediaStream | null = null;

	// Current state
	let currentStopIndex = $state(0);
	let isScanning = $state(false);
	let verificationState = $state<'idle' | 'scanning' | 'match' | 'confirmed' | 'error'>('idle');
	let matchResult = $state<{ inmate_name?: string; confidence: number } | null>(null);
	let errorMessage = $state('');
	let scanStatus = $state('Ready to scan');

	// Verification loop control
	let lastScanTime = 0;
	let animationFrameId: number | null = null;
	const SCAN_INTERVAL = 500; // ms between scans

	// Get current stop
	const currentStop = $derived<RouteStop>(() => {
		return data.rollCall.route[currentStopIndex] || data.rollCall.route[0];
	});

	// Get location name
	function getLocationName(locationId: string): string {
		const location = data.locations.find((loc) => loc.id === locationId);
		return location?.name || locationId;
	}

	// Get inmate details
	function getInmate(inmateId: string): Inmate | undefined {
		return data.inmates.find((inmate) => inmate.id === inmateId);
	}

	// Calculate progress
	const progress = $derived(() => {
		const completed = data.rollCall.route.filter((stop) => stop.status === 'completed').length;
		const total = data.rollCall.route.length;
		return {
			completed,
			total,
			percentage: total > 0 ? Math.round((completed / total) * 100) : 0
		};
	});

	// Start webcam
	async function startWebcam() {
		try {
			stream = await navigator.mediaDevices.getUserMedia({
				video: { facingMode: 'user', width: 640, height: 480 }
			});

			if (videoElement) {
				videoElement.srcObject = stream;
				await videoElement.play();
			}
		} catch (err) {
			console.error('Failed to start webcam:', err);
			errorMessage = 'Failed to access webcam. Please grant camera permissions.';
			verificationState = 'error';
		}
	}

	// Stop webcam
	function stopWebcam() {
		if (stream) {
			stream.getTracks().forEach((track) => track.stop());
			stream = null;
		}
		if (videoElement) {
			videoElement.srcObject = null;
		}
	}

	// Capture frame from video
	function captureFrame(): string | null {
		if (!videoElement || !canvasElement) return null;

		const context = canvasElement.getContext('2d');
		if (!context) return null;

		// Set canvas size to match video
		canvasElement.width = videoElement.videoWidth;
		canvasElement.height = videoElement.videoHeight;

		// Draw video frame to canvas
		context.drawImage(videoElement, 0, 0);

		// Convert to base64 JPEG
		return canvasElement.toDataURL('image/jpeg', 0.8);
	}

	// Verification loop
	async function verificationLoop() {
		if (!isScanning) {
			animationFrameId = null;
			return;
		}

		const now = Date.now();
		if (now - lastScanTime < SCAN_INTERVAL) {
			animationFrameId = requestAnimationFrame(verificationLoop);
			return;
		}

		lastScanTime = now;

		try {
			const frameData = captureFrame();
			if (!frameData) {
				animationFrameId = requestAnimationFrame(verificationLoop);
				return;
			}

			verificationState = 'scanning';
			scanStatus = '🔍 Scanning for face...';

			const result = await verifyFace(currentStop().location_id, frameData);

			if (result.matched && result.confidence >= 0.75) {
				// Match found!
				isScanning = false;
				verificationState = 'match';
				matchResult = {
					inmate_name: result.inmate_name,
					confidence: result.confidence
				};
				scanStatus = '✓ Match found!';
				animationFrameId = null;
			} else {
				// No match, continue scanning
				scanStatus = result.matched
					? `⚠ Low confidence: ${Math.round(result.confidence * 100)}%`
					: '🔍 No face detected';
				animationFrameId = requestAnimationFrame(verificationLoop);
			}
		} catch (err) {
			console.error('Verification error:', err);
			scanStatus = '❌ Verification error - retrying...';
			// Continue scanning despite error
			animationFrameId = requestAnimationFrame(verificationLoop);
		}
	}

	// Start scanning
	function handleStartScan() {
		if (isScanning) return;

		isScanning = true;
		verificationState = 'scanning';
		matchResult = null;
		errorMessage = '';
		lastScanTime = 0;

		verificationLoop();
	}

	// Stop scanning
	function handleStopScan() {
		isScanning = false;
		verificationState = 'idle';
		if (animationFrameId) {
			cancelAnimationFrame(animationFrameId);
			animationFrameId = null;
		}
	}

	// Confirm match
	function handleConfirm() {
		// In real implementation, would record verification to backend
		verificationState = 'confirmed';
		scanStatus = '✓ Verified!';

		// Auto-advance to next location after a delay
		setTimeout(() => {
			handleNextLocation();
		}, 1500);
	}

	// Retry scan
	function handleRetry() {
		matchResult = null;
		verificationState = 'idle';
		handleStartScan();
	}

	// Manual override
	function handleManualOverride() {
		// In real implementation, would show modal to select inmate and reason
		verificationState = 'confirmed';
		scanStatus = '👤 Manual override';

		setTimeout(() => {
			handleNextLocation();
		}, 1500);
	}

	// Navigate to next location
	function handleNextLocation() {
		handleStopScan();

		if (currentStopIndex < data.rollCall.route.length - 1) {
			currentStopIndex++;
			verificationState = 'idle';
			matchResult = null;
		} else {
			// Roll call complete
			handleCompleteRollCall();
		}
	}

	// Navigate to previous location
	function handlePreviousLocation() {
		handleStopScan();

		if (currentStopIndex > 0) {
			currentStopIndex--;
			verificationState = 'idle';
			matchResult = null;
		}
	}

	// Complete roll call
	async function handleCompleteRollCall() {
		try {
			await completeRollCall(data.rollCall.id);
			goto(`/rollcalls/${data.rollCall.id}`);
		} catch (err) {
			console.error('Failed to complete roll call:', err);
			errorMessage = 'Failed to complete roll call';
		}
	}

	// End early
	async function handleEndEarly() {
		if (!confirm('Are you sure you want to end this roll call early?')) {
			return;
		}

		try {
			await completeRollCall(data.rollCall.id);
			goto(`/rollcalls/${data.rollCall.id}`);
		} catch (err) {
			console.error('Failed to end roll call:', err);
			errorMessage = 'Failed to end roll call';
		}
	}

	// Lifecycle
	onMount(() => {
		startWebcam();
	});

	onDestroy(() => {
		handleStopScan();
		stopWebcam();
	});
</script>

<div class="min-h-screen bg-gray-900 text-white">
	<main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Header -->
		<div class="flex justify-between items-center mb-4">
			<h1 class="text-2xl font-bold">{data.rollCall.name}</h1>
			<button
				onclick={handleEndEarly}
				class="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium"
			>
				End Early
			</button>
		</div>

		<!-- Progress Bar -->
		<div class="mb-6">
			<div class="flex justify-between text-sm mb-2">
				<span>Progress: {progress().completed}/{progress().total} locations</span>
				<span>{progress().percentage}%</span>
			</div>
			<div class="w-full bg-gray-700 rounded-full h-3">
				<div
					class="bg-green-500 h-3 rounded-full transition-all duration-300"
					style="width: {progress().percentage}%"
				></div>
			</div>
		</div>

		<!-- Current Location Info -->
		<div class="bg-gray-800 rounded-lg p-4 mb-6">
			<h2 class="text-lg font-semibold mb-1">
				Current Location: {getLocationName(currentStop().location_id)}
			</h2>
			<p class="text-gray-400 text-sm">
				Expected:
				{#if currentStop().expected_inmates.length > 0}
					{#each currentStop().expected_inmates as inmateId, i}
						{@const inmate = getInmate(inmateId)}
						{#if inmate}
							{inmate.first_name} {inmate.last_name} (#{inmate.inmate_number}){i < currentStop().expected_inmates.length - 1 ? ', ' : ''}
						{/if}
					{/each}
				{:else}
					No prisoners expected
				{/if}
			</p>
		</div>

		<!-- Webcam and Verification Section -->
		<div class="bg-gray-800 rounded-lg p-6 mb-6">
			<div class="flex flex-col items-center">
				<!-- Video Container -->
				<div class="relative mb-4">
					<video
						bind:this={videoElement}
						class="rounded-lg border-4 {isScanning ? 'border-blue-500' : 'border-gray-600'}"
						width="640"
						height="480"
						autoplay
						playsinline
						muted
					></video>

					{#if isScanning}
						<div class="absolute inset-0 flex items-center justify-center pointer-events-none">
							<div class="border-4 border-blue-500 rounded-lg w-48 h-48 animate-pulse"></div>
						</div>
					{/if}

					<!-- Hidden canvas for frame capture -->
					<canvas bind:this={canvasElement} class="hidden"></canvas>
				</div>

				<!-- Status -->
				<p class="text-lg mb-4 {verificationState === 'error' ? 'text-red-400' : 'text-gray-300'}">
					{scanStatus}
				</p>

				<!-- Match Result -->
				{#if verificationState === 'match' && matchResult}
					<div class="bg-green-900 border-2 border-green-500 rounded-lg p-6 mb-4 max-w-md w-full">
						<h3 class="text-xl font-bold text-green-300 mb-2">✓ Match Found!</h3>
						<p class="text-lg mb-1">{matchResult.inmate_name}</p>
						<p class="text-sm text-gray-400 mb-1">
							Confidence: {Math.round(matchResult.confidence * 100)}%
						</p>
						<p class="text-green-300 font-medium">Recommendation: Confirm</p>

						<div class="flex gap-3 mt-4">
							<button
								onclick={handleConfirm}
								class="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-medium"
							>
								✓ Confirm
							</button>
							<button
								onclick={handleRetry}
								class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg"
							>
								↻ Retry
							</button>
							<button
								onclick={handleManualOverride}
								class="px-4 py-2 bg-yellow-700 hover:bg-yellow-600 rounded-lg"
							>
								Manual Override
							</button>
						</div>
					</div>
				{:else if verificationState === 'confirmed'}
					<div class="bg-green-900 border-2 border-green-500 rounded-lg p-4 mb-4">
						<p class="text-green-300 font-medium">✓ Verification recorded!</p>
					</div>
				{:else if verificationState === 'idle'}
					<button
						onclick={handleStartScan}
						class="px-8 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium text-lg"
					>
						Start Scan
					</button>
				{:else if verificationState === 'scanning'}
					<button
						onclick={handleStopScan}
						class="px-8 py-3 bg-red-600 hover:bg-red-700 rounded-lg font-medium text-lg"
					>
						Stop Scan
					</button>
				{/if}

				<!-- Error Message -->
				{#if errorMessage}
					<div class="mt-4 p-4 bg-red-900 border border-red-500 rounded-lg text-red-200">
						{errorMessage}
					</div>
				{/if}
			</div>
		</div>

		<!-- Route Progress -->
		<div class="bg-gray-800 rounded-lg p-6 mb-6">
			<h2 class="text-lg font-semibold mb-4">Route Progress</h2>
			<div class="space-y-2">
				{#each data.rollCall.route as stop, index (stop.id)}
					{@const locationName = getLocationName(stop.location_id)}
					{@const isCurrent = index === currentStopIndex}
					{@const isCompleted = stop.status === 'completed'}
					{@const isPending = !isCompleted && !isCurrent}

					<div
						class="flex items-center gap-3 p-3 rounded-lg {isCurrent ? 'bg-blue-900 border-2 border-blue-500' : isCompleted ? 'bg-green-900' : 'bg-gray-700'}"
					>
						<span class="text-2xl">
							{#if isCompleted}
								✓
							{:else if isCurrent}
								→
							{:else}
								○
							{/if}
						</span>
						<div class="flex-1">
							<div class="font-medium">{locationName}</div>
							{#if stop.expected_inmates.length > 0}
								{@const inmate = getInmate(stop.expected_inmates[0])}
								{#if inmate}
									<div class="text-sm text-gray-400">
										{inmate.first_name} {inmate.last_name}
										{stop.expected_inmates.length > 1 ? ` +${stop.expected_inmates.length - 1} more` : ''}
									</div>
								{/if}
							{/if}
						</div>
						{#if isCurrent}
							<span class="text-sm text-blue-300">Current</span>
						{:else if isCompleted}
							<span class="text-sm text-green-300">Verified</span>
						{:else}
							<span class="text-sm text-gray-400">Pending</span>
						{/if}
					</div>
				{/each}
			</div>
		</div>

		<!-- Navigation -->
		<div class="flex justify-between">
			<button
				onclick={handlePreviousLocation}
				disabled={currentStopIndex === 0}
				class="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium disabled:opacity-30 disabled:cursor-not-allowed"
			>
				← Previous Location
			</button>

			<button
				onclick={handleNextLocation}
				disabled={verificationState !== 'confirmed' && currentStopIndex === data.rollCall.route.length - 1}
				class="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium disabled:opacity-30 disabled:cursor-not-allowed"
			>
				{currentStopIndex === data.rollCall.route.length - 1 ? 'Complete Roll Call' : 'Next Location →'}
			</button>
		</div>
	</main>
</div>
