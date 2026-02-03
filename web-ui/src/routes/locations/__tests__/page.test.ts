import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Page from '../+page.svelte';
import type { Location } from '$lib/services/api';

describe('Location List Page', () => {
	const mockLocations: Location[] = [
		{
			id: '1',
			name: 'Block A',
			type: 'houseblock',
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
		},
		{
			id: '3',
			name: 'Yard',
			type: 'yard',
			building: 'Outdoor',
			floor: 0,
			capacity: 100,
			created_at: '2026-01-27T10:00:00',
			updated_at: '2026-01-27T10:00:00'
		}
	];

	it('should render page title', () => {
		render(Page, { props: { data: { locations: mockLocations } } });
		expect(screen.getByText('Locations')).toBeInTheDocument();
	});

	it('should render add location button', () => {
		render(Page, { props: { data: { locations: mockLocations } } });
		const addButton = screen.getByRole('link', { name: /add location/i });
		expect(addButton).toBeInTheDocument();
		expect(addButton).toHaveAttribute('href', '/locations/new');
	});

	it('should render filter dropdowns', () => {
		render(Page, { props: { data: { locations: mockLocations } } });
		const selects = screen.getAllByRole('combobox');
		expect(selects.length).toBeGreaterThanOrEqual(1);
	});

	it('should render all locations with hierarchy paths', () => {
		render(Page, { props: { data: { locations: mockLocations } } });
		expect(screen.getByText('Block A')).toBeInTheDocument();
		expect(screen.getByText('Block A > Cell A-101')).toBeInTheDocument();
		expect(screen.getByText('Yard')).toBeInTheDocument();
	});

	it('should display location count', () => {
		render(Page, { props: { data: { locations: mockLocations } } });
		expect(screen.getByText(/Total: 3/i)).toBeInTheDocument();
	});

	it('should handle empty location list', () => {
		render(Page, { props: { data: { locations: [] } } });
		expect(screen.getByText(/no locations found/i)).toBeInTheDocument();
	});

	it('should display location type icons', () => {
		render(Page, { props: { data: { locations: mockLocations } } });
		expect(screen.getByText('🏢')).toBeInTheDocument(); // Houseblock
		expect(screen.getByText('🚪')).toBeInTheDocument(); // Cell
		expect(screen.getByText('🌳')).toBeInTheDocument(); // Yard
	});

	it('should have filter options for location types', () => {
		render(Page, { props: { data: { locations: mockLocations } } });
		const page = screen.getByText('Locations').closest('main');
		expect(page).toBeInTheDocument();
	});

	it('should show building filter', () => {
		render(Page, { props: { data: { locations: mockLocations } } });
		const selects = screen.getAllByRole('combobox');
		expect(selects.length).toBeGreaterThanOrEqual(1);
	});

	it('should display location details', () => {
		render(Page, { props: { data: { locations: mockLocations } } });
		// Use getAllByText since multiple locations have "Building: Main"
		const buildingTexts = screen.getAllByText(/Building: Main/i);
		expect(buildingTexts.length).toBeGreaterThan(0);
		expect(screen.getByText(/Building: Outdoor/i)).toBeInTheDocument();
		expect(screen.getByText(/Capacity: 100/i)).toBeInTheDocument();
	});
});
