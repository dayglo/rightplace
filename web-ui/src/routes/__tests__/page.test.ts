import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Page from '../+page.svelte';
import type { Inmate, Location, RollCall } from '$lib/services/api';

describe('Home/Dashboard Page', () => {
	const mockInmates: Inmate[] = [
		{
			id: '1',
			inmate_number: 'A12345',
			first_name: 'John',
			last_name: 'Doe',
			date_of_birth: '1990-01-01',
			cell_block: 'A',
			cell_number: '101',
			is_enrolled: true,
			created_at: '2026-01-27T10:00:00',
			updated_at: '2026-01-27T10:00:00'
		},
		{
			id: '2',
			inmate_number: 'A12346',
			first_name: 'Jane',
			last_name: 'Smith',
			date_of_birth: '1992-05-15',
			cell_block: 'A',
			cell_number: '102',
			is_enrolled: true,
			created_at: '2026-01-27T10:00:00',
			updated_at: '2026-01-27T10:00:00'
		}
	];

	const mockLocations: Location[] = [
		{
			id: '1',
			name: 'Block A',
			type: 'block',
			building: 'Main',
			floor: 1,
			capacity: 50,
			created_at: '2026-01-27T10:00:00',
			updated_at: '2026-01-27T10:00:00'
		},
		{
			id: '2',
			name: 'Cell A-101',
			type: 'cell',
			building: 'Main',
			floor: 1,
			capacity: 1,
			parent_id: '1',
			created_at: '2026-01-27T10:00:00',
			updated_at: '2026-01-27T10:00:00'
		}
	];

	const mockRollCalls: RollCall[] = [
		{
			id: '1',
			name: 'Morning Roll Call',
			scheduled_time: '2026-01-28T09:00:00',
			status: 'completed',
			route: [],
			started_at: '2026-01-28T09:00:00',
			completed_at: '2026-01-28T09:15:00',
			created_at: '2026-01-28T08:00:00',
			updated_at: '2026-01-28T09:15:00'
		},
		{
			id: '2',
			name: 'Evening Roll Call',
			scheduled_time: '2026-01-28T17:00:00',
			status: 'in_progress',
			route: [],
			started_at: '2026-01-28T17:00:00',
			created_at: '2026-01-28T16:00:00',
			updated_at: '2026-01-28T17:05:00'
		}
	];

	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('should render page title', () => {
		render(Page, {
			props: {
				data: {
					inmates: mockInmates,
					locations: mockLocations,
					rollCalls: mockRollCalls
				}
			}
		});

		expect(screen.getByText('Prison Roll Call')).toBeInTheDocument();
	});

	it('should display prisoner count stat card', () => {
		render(Page, {
			props: {
				data: {
					inmates: mockInmates,
					locations: mockLocations,
					rollCalls: mockRollCalls
				}
			}
		});

		expect(screen.getByText('Prisoners')).toBeInTheDocument();
		expect(screen.getByText('enrolled')).toBeInTheDocument();
		// Check for 2 count - need to get the parent container
		const prisonersCard = screen.getByText('Prisoners').closest('.bg-white');
		expect(prisonersCard).toHaveTextContent('2');
	});

	it('should display location count stat card', () => {
		render(Page, {
			props: {
				data: {
					inmates: mockInmates,
					locations: mockLocations,
					rollCalls: mockRollCalls
				}
			}
		});

		expect(screen.getByText('Locations')).toBeInTheDocument();
		expect(screen.getByText('total')).toBeInTheDocument();
	});

	it('should display recent roll calls section', () => {
		render(Page, {
			props: {
				data: {
					inmates: mockInmates,
					locations: mockLocations,
					rollCalls: mockRollCalls
				}
			}
		});

		expect(screen.getByText('Recent Roll Calls')).toBeInTheDocument();
	});

	it('should display roll call cards', () => {
		render(Page, {
			props: {
				data: {
					inmates: mockInmates,
					locations: mockLocations,
					rollCalls: mockRollCalls
				}
			}
		});

		expect(screen.getByText('Morning Roll Call')).toBeInTheDocument();
		expect(screen.getByText('Evening Roll Call')).toBeInTheDocument();
	});

	it('should display quick actions section', () => {
		render(Page, {
			props: {
				data: {
					inmates: mockInmates,
					locations: mockLocations,
					rollCalls: mockRollCalls
				}
			}
		});

		expect(screen.getByText('Quick Actions')).toBeInTheDocument();
	});

	it('should display quick action buttons', () => {
		render(Page, {
			props: {
				data: {
					inmates: mockInmates,
					locations: mockLocations,
					rollCalls: mockRollCalls
				}
			}
		});

		expect(screen.getByRole('link', { name: /new prisoner/i })).toBeInTheDocument();
		expect(screen.getByRole('link', { name: /new location/i })).toBeInTheDocument();
		expect(screen.getByRole('link', { name: /create roll call/i })).toBeInTheDocument();
	});

	it('should handle empty inmates list', () => {
		render(Page, {
			props: {
				data: {
					inmates: [],
					locations: mockLocations,
					rollCalls: mockRollCalls
				}
			}
		});

		expect(screen.getByText('Prisoners')).toBeInTheDocument();
		expect(screen.getByText('enrolled')).toBeInTheDocument();
		// Check for 0 count in the Prisoners card specifically
		const prisonersCard = screen.getByText('Prisoners').closest('.bg-white');
		expect(prisonersCard).toHaveTextContent('0');
	});

	it('should handle empty locations list', () => {
		render(Page, {
			props: {
				data: {
					inmates: mockInmates,
					locations: [],
					rollCalls: mockRollCalls
				}
			}
		});

		expect(screen.getByText('Locations')).toBeInTheDocument();
		expect(screen.getByText('total')).toBeInTheDocument();
		// Check for 0 count in the Locations card specifically
		const locationsCard = screen.getByText('Locations').closest('.bg-white');
		expect(locationsCard).toHaveTextContent('0');
	});

	it('should handle empty roll calls list', () => {
		render(Page, {
			props: {
				data: {
					inmates: mockInmates,
					locations: mockLocations,
					rollCalls: []
				}
			}
		});

		expect(screen.getByText('Recent Roll Calls')).toBeInTheDocument();
		expect(screen.getByText(/no recent roll calls/i)).toBeInTheDocument();
	});
});
