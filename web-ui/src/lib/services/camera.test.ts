import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { startCamera, stopCamera, captureFrame, getCameraStatus } from './camera';

describe('Camera Service', () => {
	let mockVideoElement: HTMLVideoElement;
	let mockMediaStream: MediaStream;
	let mockTrack: MediaStreamTrack;

	beforeEach(() => {
		// Create mock video element
		mockVideoElement = document.createElement('video');
		
		// Create mock media stream track
		mockTrack = {
			stop: vi.fn(),
			kind: 'video',
			enabled: true,
			readyState: 'live'
		} as any;

		// Create mock media stream
		mockMediaStream = {
			getTracks: vi.fn(() => [mockTrack]),
			getVideoTracks: vi.fn(() => [mockTrack])
		} as any;

		// Mock getUserMedia
		global.navigator.mediaDevices = {
			getUserMedia: vi.fn()
		} as any;
	});

	afterEach(() => {
		vi.restoreAllMocks();
		stopCamera(); // Cleanup
	});

	describe('startCamera', () => {
		it('should request camera access and attach stream to video element', async () => {
			(navigator.mediaDevices.getUserMedia as any).mockResolvedValueOnce(mockMediaStream);

			const result = await startCamera(mockVideoElement);

			expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
				video: {
					width: { ideal: 1280 },
					height: { ideal: 720 },
					facingMode: 'user'
				}
			});
			expect(mockVideoElement.srcObject).toBe(mockMediaStream);
			expect(result.success).toBe(true);
		});

		it('should handle permission denied error', async () => {
			const error = new Error('Permission denied');
			error.name = 'NotAllowedError';
			(navigator.mediaDevices.getUserMedia as any).mockRejectedValueOnce(error);

			const result = await startCamera(mockVideoElement);

			expect(result.success).toBe(false);
			expect(result.error).toContain('Camera permission denied');
		});

		it('should handle no camera available error', async () => {
			const error = new Error('No camera found');
			error.name = 'NotFoundError';
			(navigator.mediaDevices.getUserMedia as any).mockRejectedValueOnce(error);

			const result = await startCamera(mockVideoElement);

			expect(result.success).toBe(false);
			expect(result.error).toContain('No camera found');
		});

		it('should handle generic errors', async () => {
			(navigator.mediaDevices.getUserMedia as any).mockRejectedValueOnce(
				new Error('Unknown error')
			);

			const result = await startCamera(mockVideoElement);

			expect(result.success).toBe(false);
			expect(result.error).toBeDefined();
		});
	});

	describe('stopCamera', () => {
		it('should stop all media tracks', async () => {
			(navigator.mediaDevices.getUserMedia as any).mockResolvedValueOnce(mockMediaStream);
			
			await startCamera(mockVideoElement);
			stopCamera();

			expect(mockTrack.stop).toHaveBeenCalled();
		});

		it('should handle being called when no camera is active', () => {
			expect(() => stopCamera()).not.toThrow();
		});

		it('should clear video element srcObject', async () => {
			(navigator.mediaDevices.getUserMedia as any).mockResolvedValueOnce(mockMediaStream);
			
			await startCamera(mockVideoElement);
			stopCamera(mockVideoElement);

			expect(mockVideoElement.srcObject).toBeNull();
		});
	});

	describe('captureFrame', () => {
		it('should capture frame as base64 JPEG', async () => {
			// Mock canvas and context
			const mockCanvas = document.createElement('canvas');
			const mockContext = {
				drawImage: vi.fn()
			};
			vi.spyOn(document, 'createElement').mockReturnValue(mockCanvas);
			vi.spyOn(mockCanvas, 'getContext').mockReturnValue(mockContext as any);
			vi.spyOn(mockCanvas, 'toDataURL').mockReturnValue('data:image/jpeg;base64,mockdata');

			// Set video dimensions
			Object.defineProperty(mockVideoElement, 'videoWidth', { value: 640 });
			Object.defineProperty(mockVideoElement, 'videoHeight', { value: 480 });

			const result = captureFrame(mockVideoElement);

			expect(mockContext.drawImage).toHaveBeenCalledWith(mockVideoElement, 0, 0);
			expect(mockCanvas.toDataURL).toHaveBeenCalledWith('image/jpeg', 0.8);
			expect(result).toBe('data:image/jpeg;base64,mockdata');
		});

		it('should use video dimensions for canvas size', () => {
			const mockCanvas = document.createElement('canvas');
			vi.spyOn(document, 'createElement').mockReturnValue(mockCanvas);
			vi.spyOn(mockCanvas, 'getContext').mockReturnValue({
				drawImage: vi.fn()
			} as any);
			vi.spyOn(mockCanvas, 'toDataURL').mockReturnValue('data:image/jpeg;base64,test');

			Object.defineProperty(mockVideoElement, 'videoWidth', { value: 1280 });
			Object.defineProperty(mockVideoElement, 'videoHeight', { value: 720 });

			captureFrame(mockVideoElement);

			expect(mockCanvas.width).toBe(1280);
			expect(mockCanvas.height).toBe(720);
		});
	});

	describe('getCameraStatus', () => {
		it('should return false when camera is not active', () => {
			expect(getCameraStatus()).toBe(false);
		});

		it('should return true when camera is active', async () => {
			(navigator.mediaDevices.getUserMedia as any).mockResolvedValueOnce(mockMediaStream);
			
			await startCamera(mockVideoElement);

			expect(getCameraStatus()).toBe(true);
		});

		it('should return false after camera is stopped', async () => {
			(navigator.mediaDevices.getUserMedia as any).mockResolvedValueOnce(mockMediaStream);
			
			await startCamera(mockVideoElement);
			stopCamera();

			expect(getCameraStatus()).toBe(false);
		});
	});
});
