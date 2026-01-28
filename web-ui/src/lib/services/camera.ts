/**
 * Camera Service for Prison Roll Call Web UI
 * 
 * Wraps browser MediaDevices API for webcam access
 */

let videoStream: MediaStream | null = null;

export interface CameraResult {
	success: boolean;
	error?: string;
}

/**
 * Start camera and attach to video element
 */
export async function startCamera(videoElement: HTMLVideoElement): Promise<CameraResult> {
	try {
		videoStream = await navigator.mediaDevices.getUserMedia({
			video: {
				width: { ideal: 1280 },
				height: { ideal: 720 },
				facingMode: 'user'
			}
		});

		videoElement.srcObject = videoStream;
		return { success: true };
	} catch (error) {
		if (error instanceof Error) {
			// Handle specific error types
			if (error.name === 'NotAllowedError') {
				return {
					success: false,
					error: 'Camera permission denied. Please allow camera access.'
				};
			}
			if (error.name === 'NotFoundError') {
				return {
					success: false,
					error: 'No camera found. Please connect a camera and try again.'
				};
			}
			return {
				success: false,
				error: error.message
			};
		}
		return {
			success: false,
			error: 'Unknown error accessing camera'
		};
	}
}

/**
 * Stop camera and release resources
 */
export function stopCamera(videoElement?: HTMLVideoElement): void {
	if (videoStream) {
		videoStream.getTracks().forEach((track) => track.stop());
		videoStream = null;
	}
	
	// Clear video element if provided
	if (videoElement) {
		videoElement.srcObject = null;
	}
}

/**
 * Capture current frame from video element as base64 JPEG
 */
export function captureFrame(videoElement: HTMLVideoElement, quality: number = 0.8): string {
	const canvas = document.createElement('canvas');
	canvas.width = videoElement.videoWidth;
	canvas.height = videoElement.videoHeight;

	const context = canvas.getContext('2d');
	if (!context) {
		throw new Error('Failed to get canvas context');
	}

	context.drawImage(videoElement, 0, 0);
	return canvas.toDataURL('image/jpeg', quality);
}

/**
 * Check if camera is currently active
 */
export function getCameraStatus(): boolean {
	return videoStream !== null;
}
