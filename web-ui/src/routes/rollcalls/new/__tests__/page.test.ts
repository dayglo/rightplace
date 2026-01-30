import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import Page from '../+page.svelte';

// Mock the navigation module
vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

describe('Create Roll Call Page', () => {
	const mockData = {
		locations: [
			{
				id: 'cell-1',
				name: 'Cell A-101',
				type: 'cell',
				building: 'Main',
				floor: 1,
				capacity: 1,
				created_at: '2026-01-01T00:00:00',
				updated_at: '2026-01-01T00:00:00'
			},
			{
				id: 'cell-2',
				name: 'Cell A-102',
				type: 'cell',
				building: 'Main',
				floor: 1,
				capacity: 1,
				created_at: '2026-01-01T00:00:00',
				updated_at: '2026-01-01T00:00:00'
			},
			{
				id: 'yard-1',
				name: 'Yard',
				type: 'yard',
				building: 'Outdoor',
				floor: 0,
				capacity: 100,
				created_at: '2026-01-01T00:00:00',
				updated_at: '2026-01-01T00:00:00'
			}
		],
		inmates: [
			{
				id: 'inmate-1',
				inmate_number: 'A12345',
				first_name: 'John',
				last_name: 'Doe',
				date_of_birth: '1990-01-01',
				cell_block: 'A',
				cell_number: '101',
				home_cell_id: 'cell-1',
				is_enrolled: true,
				created_at: '2026-01-01T00:00:00',
				updated_at: '2026-01-01T00:00:00'
			},
			{
				id: 'inmate-2',
				inmate_number: 'A12346',
				first_name: 'Jane',
				last_name: 'Smith',
				date_of_birth: '1992-01-01',
				cell_block: 'A',
				cell_number: '102',
				home_cell_id: 'cell-2',
				is_enrolled: true,
				created_at: '2026-01-01T00:00:00',
				updated_at: '2026-01-01T00:00:00'
			}
		]
	};

	it('should render form fields', () => {
		render(Page, { props: { data: mockData } });

		expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/scheduled time/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/officer id/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/notes/i)).toBeInTheDocument();
	});

	it('should display available cell locations', () => {
		render(Page, { props: { data: mockData } });

		expect(screen.getByText('Cell A-101')).toBeInTheDocument();
		expect(screen.getByText('Cell A-102')).toBeInTheDocument();
		// Yard should not be shown (filtered to cells only)
	});

	it('should show inmate count for each location', () => {
		render(Page, { props: { data: mockData } });

		// Both cells have 1 prisoner each, so "1 prisoner" appears twice
		const prisonerCounts = screen.getAllByText('1 prisoner', { exact: false });
		expect(prisonerCounts.length).toBe(2);
		expect(screen.getByText('John Doe', { exact: false })).toBeInTheDocument();
		expect(screen.getByText('Jane Smith', { exact: false })).toBeInTheDocument();
	});

	it('should allow selecting locations for route', async () => {
		render(Page, { props: { data: mockData } });

		// First checkbox is "include empty", second is first location checkbox
		const checkboxes = screen.getAllByRole('checkbox');
		const locationCheckbox = checkboxes[1]; // Skip the "include empty" checkbox
		await fireEvent.click(locationCheckbox);

		// Should appear in selected count (using getAllByText to handle multiple occurrences)
		expect(screen.getByText(/Selected: 1 location/)).toBeInTheDocument();
	});

	it('should disable generate button when no locations selected', () => {
		render(Page, { props: { data: mockData } });

		// Button should be disabled when no locations are selected
		const submitButton = screen.getByRole('button', { name: /generate route/i });
		expect(submitButton).toBeDisabled();
	});

	it('should show back button', () => {
		render(Page, { props: { data: mockData } });

		const backLinks = screen.getAllByText(/back/i);
		expect(backLinks.length).toBeGreaterThan(0);
	});
});
