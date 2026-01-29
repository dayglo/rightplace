import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Page from '../+page.svelte';

describe('Roll Calls List Page', () => {
	it('should render empty state when no roll calls', () => {
		const data = {
			rollcalls: []
		};

		render(Page, { props: { data } });

		expect(screen.getByText('No roll calls found')).toBeInTheDocument();
		expect(screen.getByText('Create your first roll call')).toBeInTheDocument();
	});

	it('should display roll calls list', () => {
		const data = {
			rollcalls: [
				{
					id: '1',
					name: 'Morning Roll Call',
					status: 'scheduled',
					scheduled_at: '2026-01-30T09:00:00',
					officer_id: 'officer1',
					notes: '',
					total_stops: 3,
					expected_inmates: 5,
					verified_inmates: 0,
					progress_percentage: 0
				},
				{
					id: '2',
					name: 'Evening Roll Call',
					status: 'in_progress',
					scheduled_at: '2026-01-30T17:00:00',
					officer_id: 'officer2',
					notes: '',
					total_stops: 2,
					expected_inmates: 3,
					verified_inmates: 2,
					progress_percentage: 50
				}
			]
		};

		render(Page, { props: { data } });

		expect(screen.getByText('Morning Roll Call')).toBeInTheDocument();
		expect(screen.getByText('Evening Roll Call')).toBeInTheDocument();
		expect(screen.getByText('Total: 2')).toBeInTheDocument();
	});

	it('should filter roll calls by status', () => {
		const data = {
			rollcalls: [
				{
					id: '1',
					name: 'Scheduled RC',
					status: 'scheduled',
					scheduled_at: '2026-01-30T09:00:00',
					officer_id: 'officer1',
					notes: '',
					total_stops: 1,
					expected_inmates: 2,
					verified_inmates: 0,
					progress_percentage: 0
				},
				{
					id: '2',
					name: 'Completed RC',
					status: 'completed',
					scheduled_at: '2026-01-29T09:00:00',
					started_at: '2026-01-29T09:00:00',
					completed_at: '2026-01-29T09:30:00',
					officer_id: 'officer1',
					notes: '',
					total_stops: 1,
					expected_inmates: 2,
					verified_inmates: 2,
					progress_percentage: 100
				}
			]
		};

		render(Page, { props: { data } });

		expect(screen.getByText('Scheduled: 1')).toBeInTheDocument();
		expect(screen.getByText('Completed: 1')).toBeInTheDocument();
	});

	it('should show create roll call button', () => {
		const data = {
			rollcalls: []
		};

		render(Page, { props: { data } });

		const createButtons = screen.getAllByText(/Create Roll Call/i);
		expect(createButtons.length).toBeGreaterThan(0);
	});
});
