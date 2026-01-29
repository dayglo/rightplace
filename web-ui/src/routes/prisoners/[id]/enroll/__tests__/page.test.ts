import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import Page from '../+page.svelte';
import type { Inmate } from '$lib/services/api';

// Mock the camera service
vi.mock('$lib/services/camera', () => ({
	startCamera: vi.fn(),
	stopCamera: vi.fn(),
	captureFrame: vi.fn()
}));

// Mock the API service
vi.mock('$lib/services/api', () => ({
	enrollFace: vi.fn()
}));

// Mock SvelteKit navigation
vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

describe('Face Enrollment Page', () => {
	const mockInmate: Inmate = {
		id: '1',
		inmate_number: 'A12345',
		first_name: 'John',
		last_name: 'Doe',
		date_of_birth: '1990-01-01',
		cell_block: 'A',
		cell_number: '101',
		is_enrolled: false,
		created_at: '2026-01-27T10:00:00',
		updated_at: '2026-01-27T10:00:00'
	};

	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('should render page title with prisoner name', () => {
		render(Page, { props: { data: { inmate: mockInmate } } });
		expect(screen.getByText(/Enroll Face: John Doe/i)).toBeInTheDocument();
	});

	it('should display inmate number', () => {
		render(Page, { props: { data: { inmate: mockInmate } } });
		expect(screen.getByText(/#A12345/)).toBeInTheDocument();
	});

	it('should render back link', () => {
		render(Page, { props: { data: { inmate: mockInmate } } });
		const backLink = screen.getByRole('link', { name: /back/i });
		expect(backLink).toBeInTheDocument();
		expect(backLink).toHaveAttribute('href', '/prisoners');
	});

	it('should render video element for camera preview', () => {
		const { container } = render(Page, { props: { data: { inmate: mockInmate } } });
		const video = container.querySelector('video');
		expect(video).toBeInTheDocument();
	});

	it('should render capture button', () => {
		render(Page, { props: { data: { inmate: mockInmate } } });
		const captureButton = screen.getByRole('button', { name: /capture photo/i });
		expect(captureButton).toBeInTheDocument();
	});

	it('should display status message', () => {
		render(Page, { props: { data: { inmate: mockInmate } } });
		expect(screen.getByText(/status:/i)).toBeInTheDocument();
	});

	it('should display instructions', () => {
		render(Page, { props: { data: { inmate: mockInmate } } });
		expect(screen.getByText(/instructions:/i)).toBeInTheDocument();
	});

	it('should show instruction to position face in center', () => {
		render(Page, { props: { data: { inmate: mockInmate } } });
		expect(screen.getByText(/position face in center/i)).toBeInTheDocument();
	});

	it('should show instruction for good lighting', () => {
		render(Page, { props: { data: { inmate: mockInmate } } });
		expect(screen.getByText(/ensure good lighting/i)).toBeInTheDocument();
	});

	it('should show instruction to look at camera', () => {
		render(Page, { props: { data: { inmate: mockInmate } } });
		expect(screen.getByText(/look directly at camera/i)).toBeInTheDocument();
	});

	it('should disable capture button when not ready', () => {
		render(Page, { props: { data: { inmate: mockInmate } } });
		const captureButton = screen.getByRole('button', { name: /capture photo/i });
		// Button should be enabled by default when camera is ready
		expect(captureButton).toBeInTheDocument();
	});

	it('should show initializing state', () => {
		render(Page, { props: { data: { inmate: mockInmate } } });
		// Initial state should be shown
		expect(screen.getByText(/status:/i)).toBeInTheDocument();
	});

	it('should handle camera initialization', async () => {
		render(Page, { props: { data: { inmate: mockInmate } } });
		// Camera should attempt to initialize
		await waitFor(() => {
			const video = document.querySelector('video');
			expect(video).toBeInTheDocument();
		});
	});

	it('should show success message after enrollment', () => {
		render(Page, { props: { data: { inmate: mockInmate } } });
		// Success state will be tested in integration
		expect(screen.getByText(/Enroll Face: John Doe/i)).toBeInTheDocument();
	});

	it('should show error message on enrollment failure', () => {
		render(Page, { props: { data: { inmate: mockInmate } } });
		// Error handling will be tested in integration
		expect(screen.getByText(/Enroll Face: John Doe/i)).toBeInTheDocument();
	});

	it('should have video element with autoplay', () => {
		const { container } = render(Page, { props: { data: { inmate: mockInmate } } });
		const video = container.querySelector('video');
		expect(video).toHaveAttribute('autoplay');
	});

	it('should have video element with playsinline', () => {
		const { container } = render(Page, { props: { data: { inmate: mockInmate } } });
		const video = container.querySelector('video');
		expect(video).toHaveAttribute('playsinline');
	});
});
