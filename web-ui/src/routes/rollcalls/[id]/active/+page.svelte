<script lang="ts">
	import type { PageData } from './$types';
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { verifyFace, completeRollCall, recordVerification } from '$lib/services/api';
	import type { Location, Inmate, RouteStop } from '$lib/services/api';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// Video and canvas refs
	let videoElement: HTMLVideoElement;
	let canvasElement: HTMLCanvasElement;
	let overlayCanvasElement: HTMLCanvasElement;
	let stream: MediaStream | null = null;

	// Current state
	let currentStopIndex = $state(0);
	let isScanning = $state(false);
	let isSavingVerification = $state(false);
	let verificationState = $state<'idle' | 'scanning' | 'match' | 'confirmed' | 'error'>('idle');
	let matchResult = $state<{ inmate_id?: string; inmate_name?: string; confidence: number } | null>(null);
	let errorMessage = $state('');
	let scanStatus = $state('Ready to scan');
	let detailedStatus = $state('Idle');
	let lastDetection = $state<any>(null);

	/**
	 * Local verification state (combines loaded verifications + newly created ones)
	 *
	 * This is essential for immediate UI updates:
	 * - Starts with verifications loaded from database (data.existingVerifications)
	 * - When user confirms a verification, we add it to this array immediately
	 * - This ensures duplicate checks work without page reload
	 * - Counts update instantly in the UI
	 * - "Already verified" section shows newly created verifications
	 */
	let allVerifications = $state(data.existingVerifications || []);

	// Frozen face queue
	interface FrozenFaceItem {
		id: string;
		imageData: ImageData;
		result: 'pending' | 'match' | 'no_match';
		inmateName?: string;
		inmateNumber?: string;
		confidence?: number;
		timestamp: number;
	}
	let frozenFaceQueue = $state<FrozenFaceItem[]>([]);

	// Verification loop control
	let lastScanTime = 0;
	let animationFrameId: number | null = null;
	const SCAN_INTERVAL = 500; // ms between scans

	// Svelte action to draw canvas when bound
	function drawCanvas(canvas: HTMLCanvasElement, faceItem: FrozenFaceItem) {
		drawFrozenFaceById(canvas, faceItem);

		return {
			update(newFaceItem: FrozenFaceItem) {
				drawFrozenFaceById(canvas, newFaceItem);
			}
		};
	}

	// Get current stop
	const currentStop = $derived(data.rollCall.route[currentStopIndex] || data.rollCall.route[0]);

	// Get location name
	function getLocationName(locationId: string): string {
		const location = data.locations.find((loc) => loc.id === locationId);
		return location?.name || locationId;
	}

	// Get inmate details
	function getInmate(inmateId: string): Inmate | undefined {
		return data.inmates.find((inmate) => inmate.id === inmateId);
	}

	// Format timestamp for display
	function formatTimestamp(timestamp: string): string {
		const date = new Date(timestamp);
		const now = new Date();
		const diffMinutes = Math.floor((now.getTime() - date.getTime()) / 60000);

		if (diffMinutes < 1) return 'just now';
		if (diffMinutes < 60) return `${diffMinutes}m ago`;

		const diffHours = Math.floor(diffMinutes / 60);
		if (diffHours < 24) return `${diffHours}h ago`;

		return date.toLocaleDateString();
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

	/**
	 * Calculate verification counts for current location
	 *
	 * Two sources of verified inmates:
	 * 1. currentSessionCount: Faces in the visual queue with result='match'
	 *    - These are verifications just performed in this session
	 *    - User can see their faces on screen
	 *
	 * 2. existingCount: Verifications from database + newly saved ones
	 *    - Loaded when page first loads (from database)
	 *    - Updated immediately when user confirms (added to allVerifications)
	 *    - Displayed in "Already verified" section below location info
	 *
	 * Why we need both:
	 * - Visual queue shows faces captured in current session
	 * - But on page reload, we don't have those face images
	 * - So we track database verifications separately
	 * - Total count = currentSessionCount + existingCount
	 *
	 * Auto-advance logic:
	 * - When verifiedCount === expectedCount, auto-advance to next location
	 * - This works correctly even after page reload because existingCount persists
	 */
	const verificationCounts = $derived(() => {
		const currentSessionCount = frozenFaceQueue.filter(f => f.result === 'match').length;

		const currentLocationId = currentStop.location_id;
		const existingCount = allVerifications
			.filter(v => v.location_id === currentLocationId && v.status === 'verified')
			.length;

		const verifiedCount = currentSessionCount + existingCount;
		const expectedCount = currentStop.expected_inmates.length;
		return { verifiedCount, expectedCount, existingCount, currentSessionCount };
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

	// Draw face bounding box on overlay
	function drawFaceBounds(detection: any) {
		if (!overlayCanvasElement || !videoElement) return;

		const canvas = overlayCanvasElement;
		const ctx = canvas.getContext('2d');
		if (!ctx) return;

		// Clear previous drawings
		ctx.clearRect(0, 0, canvas.width, canvas.height);

		if (!detection || !detection.bounding_box) return;

		const box = detection.bounding_box;

		// Draw bounding box
		ctx.strokeStyle = detection.detected && detection.quality > 0.5 ? '#10b981' : '#ef4444';
		ctx.lineWidth = 3;
		ctx.strokeRect(box.x, box.y, box.width, box.height);

		// Draw quality indicator
		if (detection.detected) {
			const qualityColor = detection.quality > 0.7 ? '#10b981' : detection.quality > 0.4 ? '#f59e0b' : '#ef4444';
			ctx.fillStyle = qualityColor;
			ctx.font = '14px sans-serif';
			ctx.fillText(`Quality: ${Math.round(detection.quality * 100)}%`, box.x, box.y - 10);
		}

		// Draw landmarks if available
		if (detection.landmarks) {
			ctx.fillStyle = '#3b82f6';
			const landmarks = detection.landmarks;
			[landmarks.left_eye, landmarks.right_eye, landmarks.nose, landmarks.left_mouth, landmarks.right_mouth].forEach(([x, y]) => {
				ctx.beginPath();
				ctx.arc(x, y, 3, 0, 2 * Math.PI);
				ctx.fill();
			});
		}
	}

	// Capture and freeze the detected face region
	function freezeFaceRegion(detection: any): ImageData | null {
		if (!canvasElement || !detection || !detection.bounding_box) return null;

		const ctx = canvasElement.getContext('2d');
		if (!ctx) return null;

		const box = detection.bounding_box;

		// Add padding around the face (20%)
		const padding = 0.2;
		const paddedWidth = box.width * (1 + padding * 2);
		const paddedHeight = box.height * (1 + padding * 2);
		const paddedX = Math.max(0, box.x - box.width * padding);
		const paddedY = Math.max(0, box.y - box.height * padding);

		// Extract the face region
		return ctx.getImageData(paddedX, paddedY, paddedWidth, paddedHeight);
	}

	// Draw frozen face on canvas by ID
	function drawFrozenFaceById(canvasElement: HTMLCanvasElement, faceItem: FrozenFaceItem) {
		if (!canvasElement || !faceItem) return;

		const ctx = canvasElement.getContext('2d');
		if (!ctx) return;

		// Set canvas size to match frozen face
		canvasElement.width = faceItem.imageData.width;
		canvasElement.height = faceItem.imageData.height;

		// Draw the frozen face
		ctx.putImageData(faceItem.imageData, 0, 0);
	}

	// Add face to queue
	function addFaceToQueue(imageData: ImageData, result: 'pending' | 'match' | 'no_match', inmateName?: string, inmateNumber?: string, confidence?: number) {
		// Check if this inmate is already in the queue (prevent duplicates)
		if (result === 'match' && inmateName) {
			const existingIndex = frozenFaceQueue.findIndex(f => f.inmateName === inmateName);
			if (existingIndex !== -1) {
				// Update existing entry instead of adding new one
				frozenFaceQueue = frozenFaceQueue.map((face, idx) =>
					idx === existingIndex
						? { ...face, imageData, result, inmateNumber, confidence, timestamp: Date.now() }
						: face
				);
				return;
			}
		}

		const id = `face-${Date.now()}-${Math.random()}`;
		const newFace: FrozenFaceItem = {
			id,
			imageData,
			result,
			inmateName,
			inmateNumber,
			confidence,
			timestamp: Date.now()
		};

		frozenFaceQueue = [...frozenFaceQueue, newFace];

		// Auto-remove no-match faces after 10 seconds
		if (result === 'no_match') {
			setTimeout(() => {
				frozenFaceQueue = frozenFaceQueue.filter(f => f.id !== id);
			}, 10000); // Show for 10 seconds then remove
		}
	}

	// Update face result in queue
	function updateFaceResult(id: string, result: 'match' | 'no_match', inmateName?: string, inmateNumber?: string, confidence?: number) {
		// If it's a match, check for duplicates first
		if (result === 'match' && inmateName) {
			const existingMatch = frozenFaceQueue.find(f => f.inmateName === inmateName && f.id !== id);
			if (existingMatch) {
				// Remove the pending one, keep the existing match
				frozenFaceQueue = frozenFaceQueue.filter(f => f.id !== id);
				return;
			}
		}

		frozenFaceQueue = frozenFaceQueue.map(face =>
			face.id === id
				? { ...face, result, inmateName, inmateNumber, confidence }
				: face
		);

		// Auto-remove if no match after 10 seconds
		if (result === 'no_match') {
			setTimeout(() => {
				frozenFaceQueue = frozenFaceQueue.filter(f => f.id !== id);
			}, 10000);
		}
	}

	// Clear queue when moving to new location
	function clearFaceQueue() {
		frozenFaceQueue = [];
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
			// Step 1: Capture frame
			detailedStatus = '📸 Capturing frame...';
			const frameData = captureFrame();
			if (!frameData) {
				detailedStatus = '⚠ No video frame available';
				animationFrameId = requestAnimationFrame(verificationLoop);
				return;
			}

			// Step 2: Send to server
			verificationState = 'scanning';
			scanStatus = '🔍 Scanning for face...';
			detailedStatus = '📤 Sending image to server...';

			const startTime = Date.now();
			const result = await verifyFace(currentStop.location_id, data.rollCall.id, frameData);
			const responseTime = Date.now() - startTime;

			// Step 3: Process result
			detailedStatus = `✅ Server response received (${responseTime}ms)`;

			// Store and draw detection
			let currentFaceId: string | null = null;
			if (result.detection) {
				lastDetection = result.detection;
				drawFaceBounds(result.detection);

				// Freeze the face region if detected
				if (result.detection.detected && result.detection.bounding_box) {
					const faceImage = freezeFaceRegion(result.detection);
					if (faceImage) {
						addFaceToQueue(faceImage, 'pending');
						currentFaceId = frozenFaceQueue[frozenFaceQueue.length - 1]?.id || null;
					}
				}

				// Update status based on detection
				if (!result.detection.detected) {
					detailedStatus = '❌ No face detected in frame';
				} else if (result.detection.face_count > 1) {
					detailedStatus = `⚠ Multiple faces detected (${result.detection.face_count})`;
				} else if (result.detection.quality_issues && result.detection.quality_issues.length > 0) {
					const issues = result.detection.quality_issues.join(', ');
					detailedStatus = `⚠ Quality issues: ${issues}`;
				} else {
					detailedStatus = `✓ Face detected (quality: ${Math.round(result.detection.quality * 100)}%)`;
				}
			}

			if (result.matched && result.confidence >= 0.75) {
				// Match found!
				isScanning = false;
				verificationState = 'match';

				// Get inmate details for prisoner number
				const inmateId = result.inmate_id;
				const inmate = inmateId ? getInmate(inmateId) : undefined;
				const inmateNumber = inmate?.inmate_number;

				matchResult = {
					inmate_id: result.inmate_id,
					inmate_name: result.inmate_name,
					confidence: result.confidence
				};
				scanStatus = '✓ Match found!';
				detailedStatus = `✓ Matched: ${result.inmate_name} (${Math.round(result.confidence * 100)}%)`;

				// Update frozen face to show match
				if (currentFaceId) {
					updateFaceResult(currentFaceId, 'match', result.inmate_name, inmateNumber, result.confidence);
				}

				animationFrameId = null;
			} else {
				// No match or low confidence
				if (currentFaceId) {
					updateFaceResult(currentFaceId, 'no_match');
				}

				scanStatus = result.matched
					? `⚠ Low confidence: ${Math.round(result.confidence * 100)}%`
					: '🔍 No face detected';

				animationFrameId = requestAnimationFrame(verificationLoop);
			}
		} catch (err) {
			console.error('Verification error:', err);
			scanStatus = '❌ Verification error - retrying...';
			detailedStatus = `❌ Error: ${err instanceof Error ? err.message : 'Unknown error'}`;

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
		detailedStatus = 'Starting verification...';
		lastDetection = null;

		verificationLoop();
	}

	// Stop scanning
	function handleStopScan() {
		isScanning = false;
		verificationState = 'idle';
		detailedStatus = 'Idle';

		// Clear overlay canvas
		if (overlayCanvasElement) {
			const ctx = overlayCanvasElement.getContext('2d');
			if (ctx) {
				ctx.clearRect(0, 0, overlayCanvasElement.width, overlayCanvasElement.height);
			}
		}

		if (animationFrameId) {
			cancelAnimationFrame(animationFrameId);
			animationFrameId = null;
		}
	}

	/**
	 * Confirm match and save verification to backend
	 *
	 * Flow:
	 * 1. Validate we have a match result with inmate_id
	 * 2. Check for duplicates (same inmate already verified at this location)
	 * 3. Save verification to backend via API
	 * 4. Update local state (add to allVerifications array)
	 * 5. Decide next action based on expected count:
	 *    - If more inmates expected: resume scanning
	 *    - If all verified: auto-advance to next location
	 *
	 * Error handling:
	 * - Network errors: Show error message, keep state, allow retry
	 * - Don't advance if save fails
	 * - Buttons disabled during save to prevent double-submit
	 *
	 * State updates:
	 * - allVerifications: Add new verification immediately (before auto-advance)
	 * - This ensures duplicate check works even if user confirms quickly
	 * - Counts update instantly without page reload
	 */
	async function handleConfirm() {
		if (!matchResult || !matchResult.inmate_id) {
			errorMessage = 'No match result available to confirm';
			return;
		}

		// Duplicate check: Prevent verifying same inmate twice at same location
		const currentLocationId = currentStop.location_id;
		const alreadyVerified = allVerifications.some(
			v => v.inmate_id === matchResult!.inmate_id &&
			     v.location_id === currentLocationId &&
			     v.status === 'verified'
		);

		if (alreadyVerified) {
			errorMessage = 'This inmate was already verified at this location';
			return;
		}

		try {
			// Show loading state (disables buttons to prevent navigation during save)
			isSavingVerification = true;

			// Save to backend
			const newVerification = await recordVerification(data.rollCall.id, {
				inmate_id: matchResult.inmate_id,
				location_id: currentStop.location_id,
				status: 'verified',
				confidence: matchResult.confidence,
				is_manual_override: false,
				notes: ''
			});

			// CRITICAL: Update local state immediately
			// This ensures duplicate check works for next verification without reload
			allVerifications = [...allVerifications, newVerification];

			scanStatus = '✓ Verified!';
			detailedStatus = '✓ Verification confirmed and saved to database';
			errorMessage = '';

			// Decide next action based on verification counts
			const counts = verificationCounts();

			if (counts.verifiedCount < counts.expectedCount) {
				// More inmates expected at this location - continue scanning
				verificationState = 'idle';
				matchResult = null;
				setTimeout(() => {
					handleStartScan();
				}, 500);
			} else {
				// All expected inmates verified - auto-advance to next location
				verificationState = 'confirmed';
				setTimeout(() => {
					handleNextLocation();
				}, 1500);
			}
		} catch (err) {
			console.error('Failed to record verification:', err);
			errorMessage = 'Failed to save verification. Please try again.';
			// Don't advance on error - let user retry
		} finally {
			isSavingVerification = false;
		}
	}

	// Retry scan
	function handleRetry() {
		matchResult = null;
		lastDetection = null;
		verificationState = 'idle';
		scanStatus = 'Ready to scan';
		// Don't clear queue - keep previous matches visible
		handleStartScan();
	}

	// Manual override
	function handleManualOverride() {
		// In real implementation, would show modal to select inmate and reason
		verificationState = 'confirmed';
		scanStatus = '👤 Manual override';
		detailedStatus = '👤 Manual verification recorded';

		setTimeout(() => {
			handleNextLocation();
		}, 1500);
	}

	// Skip location (prisoner not present)
	function handleSkipLocation() {
		handleStopScan();
		verificationState = 'confirmed';
		scanStatus = '⏭ Location skipped';
		detailedStatus = '⏭ Location marked as complete (prisoner not present)';

		setTimeout(() => {
			handleNextLocation();
		}, 800);
	}

	// Navigate to next location
	function handleNextLocation() {
		handleStopScan();

		if (currentStopIndex < data.rollCall.route.length - 1) {
			currentStopIndex++;
			verificationState = 'idle';
			matchResult = null;
			lastDetection = null;
			clearFaceQueue();
			scanStatus = 'Ready to scan';
			detailedStatus = 'Idle';
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
			lastDetection = null;
			clearFaceQueue();
			scanStatus = 'Ready to scan';
			detailedStatus = 'Idle';
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
			<div class="flex justify-between items-start gap-4">
				<div class="flex-1">
					<div class="flex items-center gap-3 mb-2">
						<h2 class="text-lg font-semibold">
							Current Location: {getLocationName(currentStop.location_id)}
						</h2>
						<!-- Verification Progress Badge -->
						{#if verificationCounts().expectedCount > 0}
							<span
								class="px-3 py-1 rounded-full text-sm font-bold"
								class:bg-green-600={verificationCounts().verifiedCount === verificationCounts().expectedCount}
								class:bg-yellow-600={verificationCounts().verifiedCount > 0 && verificationCounts().verifiedCount < verificationCounts().expectedCount}
								class:bg-gray-600={verificationCounts().verifiedCount === 0}
							>
								{verificationCounts().verifiedCount}/{verificationCounts().expectedCount}
							</span>
						{/if}
					</div>
					<p class="text-gray-400 text-sm mb-2">
						Expected:
						{#if currentStop.expected_inmates.length > 0}
							{#each currentStop.expected_inmates as inmateId, i}
								{@const inmate = getInmate(inmateId)}
								{#if inmate}
									{inmate.first_name} {inmate.last_name} (#{inmate.inmate_number}){i < currentStop.expected_inmates.length - 1 ? ', ' : ''}
								{/if}
							{/each}
						{:else}
							No prisoners expected
						{/if}
					</p>
					{#if verificationCounts().existingCount > 0}
						{@const currentLocationId = currentStop.location_id}
						{@const existingVerifiedInmates = allVerifications.filter(
							v => v.location_id === currentLocationId && v.status === 'verified'
						)}
						<div class="text-green-400 text-sm space-y-1">
							<p class="font-semibold">✓ Already verified ({verificationCounts().existingCount}):</p>
							{#each existingVerifiedInmates as verification}
								{@const inmate = getInmate(verification.inmate_id)}
								{#if inmate}
									<p class="pl-4">
										• {inmate.first_name} {inmate.last_name} (#{inmate.inmate_number})
										<span class="text-gray-400 text-xs">- {formatTimestamp(verification.timestamp)}</span>
									</p>
								{/if}
							{/each}
						</div>
					{/if}
				</div>

				<!-- Prominent Skip Button -->
				{#if verificationState !== 'confirmed'}
					<button
						onclick={handleSkipLocation}
						disabled={isSavingVerification}
						class="px-6 py-3 bg-orange-600 hover:bg-orange-700 rounded-lg font-medium whitespace-nowrap shadow-lg transition-all hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
					>
						⏭ Skip Location
					</button>
				{/if}
			</div>
		</div>

		<!-- Verified Faces Gallery (Horizontal Scroll) -->
		{#if frozenFaceQueue.length > 0}
			<div class="bg-gray-800 rounded-lg p-4 mb-6">
				<div class="flex justify-between items-center mb-3">
					<h3 class="text-lg font-semibold">
						Verified: {verificationCounts().verifiedCount} / {verificationCounts().expectedCount}
					</h3>
					<span class="text-sm text-gray-400">Swipe to view all →</span>
				</div>
				<!-- Horizontal scrollable container -->
				<div class="overflow-x-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
					<div class="flex gap-4 pb-2" style="min-width: min-content;">
						{#each frozenFaceQueue as faceItem (faceItem.id)}
							<div
								class="relative rounded-xl overflow-hidden shadow-2xl transition-all duration-300 ease-out flex-shrink-0"
								class:border-6={faceItem.result !== 'pending'}
								class:border-yellow-500={faceItem.result === 'pending'}
								class:border-green-500={faceItem.result === 'match'}
								class:border-red-500={faceItem.result === 'no_match'}
								class:animate-pulse-border={faceItem.result === 'pending'}
								class:animate-glow-green={faceItem.result === 'match'}
								class:animate-flash-red={faceItem.result === 'no_match'}
								class:animate-fade-out={faceItem.result === 'no_match'}
								style="border-width: {faceItem.result === 'pending' ? '4px' : '6px'}; width: 180px;"
							>
								<canvas
									use:drawCanvas={faceItem}
									class="block w-full"
									style="image-rendering: crisp-edges;"
								></canvas>

								<!-- Processing overlay -->
								{#if faceItem.result === 'pending'}
									<div class="absolute inset-0 bg-black bg-opacity-30 flex items-center justify-center">
										<div class="flex flex-col items-center gap-1">
											<div class="w-6 h-6 border-3 border-yellow-500 border-t-transparent rounded-full animate-spin"></div>
											<span class="text-yellow-300 font-semibold text-xs">Analyzing</span>
										</div>
									</div>
								{/if}

								<!-- Match result overlay -->
								{#if faceItem.result === 'match'}
									<div class="absolute inset-0 bg-gradient-to-t from-green-900/90 via-green-900/20 to-transparent flex flex-col items-center justify-end pb-1">
										<div class="bg-green-600 px-2 py-0.5 rounded-full shadow-lg mb-1">
											<span class="text-white font-bold text-xs">✓ VERIFIED</span>
										</div>
										{#if faceItem.inmateName}
											<div class="text-center bg-black/70 px-2 py-1 rounded w-full">
												<div class="text-white text-xs font-bold leading-tight">{faceItem.inmateName}</div>
												{#if faceItem.inmateNumber}
													<div class="text-green-300 text-xs font-semibold">#{faceItem.inmateNumber}</div>
												{/if}
											</div>
										{/if}
									</div>
								{/if}

								{#if faceItem.result === 'no_match'}
									<div class="absolute inset-0 bg-gradient-to-t from-red-900 via-transparent to-transparent flex items-end justify-center pb-2">
										<div class="bg-red-600 px-2 py-1 rounded-full shadow-lg">
											<span class="text-white font-bold text-xs">✗ NO MATCH</span>
										</div>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			</div>
		{/if}

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

					<!-- Overlay canvas for face bounds -->
					<canvas
						bind:this={overlayCanvasElement}
						class="absolute top-0 left-0 rounded-lg pointer-events-none"
						width="640"
						height="480"
					></canvas>

					<!-- Hidden canvas for frame capture -->
					<canvas bind:this={canvasElement} class="hidden"></canvas>
				</div>
			</div>

			<div class="flex flex-col items-center mt-6">

				<!-- Status Bar -->
				<div class="w-full max-w-2xl mb-4">
					<div class="bg-gray-900 rounded-lg p-4 border-2 {isScanning ? 'border-blue-500' : 'border-gray-700'}">
						<div class="flex items-center justify-between mb-2">
							<p class="text-lg font-semibold {verificationState === 'error' ? 'text-red-400' : 'text-gray-300'}">
								{scanStatus}
							</p>
							{#if isScanning}
								<div class="flex items-center gap-2">
									<div class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
									<span class="text-sm text-blue-400">Processing</span>
								</div>
							{/if}
						</div>
						<p class="text-sm text-gray-400 font-mono">
							{detailedStatus}
						</p>
						{#if lastDetection && lastDetection.quality_issues && lastDetection.quality_issues.length > 0}
							<div class="mt-2 flex flex-wrap gap-1">
								{#each lastDetection.quality_issues as issue}
									<span class="px-2 py-1 bg-yellow-900 text-yellow-200 text-xs rounded">
										{issue.replace('_', ' ')}
									</span>
								{/each}
							</div>
						{/if}
					</div>
				</div>

				<!-- Match Result -->
				{#if verificationState === 'match' && matchResult}
					{#key verificationCounts().verifiedCount}
						{@const moreToVerify = verificationCounts().verifiedCount < verificationCounts().expectedCount}
						<div class="bg-green-900 border-2 border-green-500 rounded-lg p-6 mb-4 max-w-md w-full">
							<h3 class="text-xl font-bold text-green-300 mb-2">✓ Match Found!</h3>
							<p class="text-lg mb-1">{matchResult.inmate_name}</p>
							<p class="text-sm text-gray-400 mb-1">
								Confidence: {Math.round(matchResult.confidence * 100)}%
							</p>
							<p class="text-green-300 font-medium">Recommendation: Confirm</p>

							{#if moreToVerify}
								<p class="text-yellow-300 text-sm mt-2">
									📋 {verificationCounts().expectedCount - verificationCounts().verifiedCount} more to verify at this location
								</p>
							{/if}

							<div class="flex gap-3 mt-4">
								<button
									onclick={handleConfirm}
									disabled={isSavingVerification}
									class="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
								>
									{#if isSavingVerification}
										<div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
										Saving...
									{:else}
										✓ {moreToVerify ? 'Confirm & Continue' : 'Confirm & Next Location'}
									{/if}
								</button>
								<button
									onclick={handleRetry}
									disabled={isSavingVerification}
									class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
								>
									↻ Retry
								</button>
							</div>
						</div>
					{/key}
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
				disabled={currentStopIndex === 0 || isSavingVerification}
				class="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium disabled:opacity-30 disabled:cursor-not-allowed"
			>
				← Previous Location
			</button>

			<button
				onclick={handleNextLocation}
				disabled={(verificationState !== 'confirmed' && currentStopIndex === data.rollCall.route.length - 1) || isSavingVerification}
				class="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium disabled:opacity-30 disabled:cursor-not-allowed"
			>
				{currentStopIndex === data.rollCall.route.length - 1 ? 'Complete Roll Call' : 'Next Location →'}
			</button>
		</div>
	</main>
</div>

<style>
	@keyframes scale-in {
		from {
			transform: scale(0.8);
			opacity: 0;
		}
		to {
			transform: scale(1);
			opacity: 1;
		}
	}

	@keyframes pulse-border {
		0%, 100% {
			border-color: rgb(234, 179, 8);
			box-shadow: 0 0 20px rgba(234, 179, 8, 0.5);
		}
		50% {
			border-color: rgb(250, 204, 21);
			box-shadow: 0 0 30px rgba(250, 204, 21, 0.8);
		}
	}

	@keyframes glow-green {
		0% {
			box-shadow: 0 0 20px rgba(34, 197, 94, 0.5);
		}
		50% {
			box-shadow: 0 0 40px rgba(34, 197, 94, 0.9), 0 0 60px rgba(34, 197, 94, 0.6);
		}
		100% {
			box-shadow: 0 0 20px rgba(34, 197, 94, 0.5);
		}
	}

	@keyframes flash-red {
		0%, 100% {
			box-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
		}
		25% {
			box-shadow: 0 0 40px rgba(239, 68, 68, 0.9), 0 0 60px rgba(239, 68, 68, 0.6);
		}
		50% {
			box-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
		}
	}

	.animate-scale-in {
		animation: scale-in 0.3s ease-out;
	}

	.animate-pulse-border {
		animation: pulse-border 1.5s ease-in-out infinite;
	}

	.animate-glow-green {
		animation: glow-green 1.5s ease-in-out 2;
	}

	.animate-flash-red {
		animation: flash-red 0.5s ease-in-out 3;
	}

	@keyframes fade-out {
		0% {
			opacity: 1;
			transform: scale(1);
		}
		70% {
			opacity: 0.6;
			transform: scale(0.98);
		}
		100% {
			opacity: 0;
			transform: scale(0.95);
		}
	}

	.animate-fade-out {
		animation: fade-out 1.5s ease-out forwards;
	}

	/* Scrollbar styling for horizontal gallery */
	.scrollbar-thin {
		scrollbar-width: thin;
	}

	.scrollbar-thin::-webkit-scrollbar {
		height: 8px;
	}

	.scrollbar-thin::-webkit-scrollbar-track {
		background: #1f2937;
		border-radius: 4px;
	}

	.scrollbar-thin::-webkit-scrollbar-thumb {
		background: #4b5563;
		border-radius: 4px;
	}

	.scrollbar-thin::-webkit-scrollbar-thumb:hover {
		background: #6b7280;
	}

	/* Smooth scroll behavior */
	.overflow-x-auto {
		scroll-behavior: smooth;
		-webkit-overflow-scrolling: touch;
	}
</style>
