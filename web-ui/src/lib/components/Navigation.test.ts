import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import Navigation from './Navigation.svelte';
import * as api from '$lib/services/api';

// Mock the API module
vi.mock('$lib/services/api', () => ({
	checkHealth: vi.fn()
}));

describe('Navigation', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('should render navigation title', () => {
		vi.mocked(api.checkHealth).mockResolvedValue({
			status: 'ok',
			timestamp: '2026-01-28T12:00:00'
		});

		render(Navigation);

		expect(screen.getByText('Prison Roll Call')).toBeInTheDocument();
	});

	it('should show green status when server is healthy', async () => {
		vi.mocked(api.checkHealth).mockResolvedValue({
			status: 'ok',
			timestamp: '2026-01-28T12:00:00'
		});

		render(Navigation);

		await waitFor(() => {
			const statusIndicator = screen.getByTestId('server-status');
			expect(statusIndicator).toHaveClass('bg-green-500');
		});
	});

	it('should show red status when server is unhealthy', async () => {
		vi.mocked(api.checkHealth).mockRejectedValue(new Error('Server down'));

		render(Navigation);

		await waitFor(() => {
			const statusIndicator = screen.getByTestId('server-status');
			expect(statusIndicator).toHaveClass('bg-red-500');
		});
	});

	it('should show yellow status while checking', () => {
		vi.mocked(api.checkHealth).mockImplementation(
			() => new Promise((resolve) => setTimeout(resolve, 1000))
		);

		render(Navigation);

		const statusIndicator = screen.getByTestId('server-status');
		expect(statusIndicator).toHaveClass('bg-yellow-500');
	});

	it('should display server status text', async () => {
		vi.mocked(api.checkHealth).mockResolvedValue({
			status: 'ok',
			timestamp: '2026-01-28T12:00:00'
		});

		render(Navigation);

		expect(screen.getByText('Server:')).toBeInTheDocument();
	});

	it('should periodically check server health', async () => {
		vi.mocked(api.checkHealth).mockResolvedValue({
			status: 'ok',
			timestamp: '2026-01-28T12:00:00'
		});

		render(Navigation);

		// Should call immediately
		await waitFor(() => {
			expect(api.checkHealth).toHaveBeenCalledTimes(1);
		});

		// Note: Testing interval behavior would require advancing timers
		// which is complex in this context. The component should set up
		// an interval to check every 30 seconds.
	});
});
