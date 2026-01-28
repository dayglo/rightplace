import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import RollCallCard from './RollCallCard.svelte';

describe('RollCallCard', () => {
	it('should render roll call name', () => {
		render(RollCallCard, {
			props: {
				rollCall: {
					id: '1',
					name: 'Morning Roll Call',
					status: 'completed',
					scheduled_time: '2026-01-28T09:00:00',
					route: [],
					created_at: '2026-01-28T08:00:00',
					updated_at: '2026-01-28T09:15:00'
				},
				verifiedCount: 5,
				totalCount: 5
			}
		});

		expect(screen.getByText('Morning Roll Call')).toBeInTheDocument();
	});

	it('should render completed status', () => {
		render(RollCallCard, {
			props: {
				rollCall: {
					id: '1',
					name: 'Morning Roll Call',
					status: 'completed',
					scheduled_time: '2026-01-28T09:00:00',
					route: [],
					created_at: '2026-01-28T08:00:00',
					updated_at: '2026-01-28T09:15:00'
				},
				verifiedCount: 5,
				totalCount: 5
			}
		});

		expect(screen.getByText(/completed/i)).toBeInTheDocument();
	});

	it('should render in progress status', () => {
		render(RollCallCard, {
			props: {
				rollCall: {
					id: '2',
					name: 'Evening Roll Call',
					status: 'in_progress',
					scheduled_time: '2026-01-28T17:00:00',
					route: [],
					created_at: '2026-01-28T16:00:00',
					updated_at: '2026-01-28T17:05:00'
				},
				verifiedCount: 2,
				totalCount: 5
			}
		});

		expect(screen.getByText(/in progress/i)).toBeInTheDocument();
	});

	it('should render verification count', () => {
		render(RollCallCard, {
			props: {
				rollCall: {
					id: '1',
					name: 'Morning Roll Call',
					status: 'completed',
					scheduled_time: '2026-01-28T09:00:00',
					route: [],
					created_at: '2026-01-28T08:00:00',
					updated_at: '2026-01-28T09:15:00'
				},
				verifiedCount: 5,
				totalCount: 5
			}
		});

		expect(screen.getByText('5/5 verified')).toBeInTheDocument();
	});

	it('should render partial verification count', () => {
		render(RollCallCard, {
			props: {
				rollCall: {
					id: '2',
					name: 'Evening Roll Call',
					status: 'in_progress',
					scheduled_time: '2026-01-28T17:00:00',
					route: [],
					created_at: '2026-01-28T16:00:00',
					updated_at: '2026-01-28T17:05:00'
				},
				verifiedCount: 2,
				totalCount: 5
			}
		});

		expect(screen.getByText('2/5 verified')).toBeInTheDocument();
	});

	it('should format scheduled time', () => {
		render(RollCallCard, {
			props: {
				rollCall: {
					id: '1',
					name: 'Morning Roll Call',
					status: 'completed',
					scheduled_time: '2026-01-28T09:00:00',
					route: [],
					created_at: '2026-01-28T08:00:00',
					updated_at: '2026-01-28T09:15:00'
				},
				verifiedCount: 5,
				totalCount: 5
			}
		});

		// Should display formatted date/time
		expect(screen.getByText(/Jan 28/i)).toBeInTheDocument();
	});
});
