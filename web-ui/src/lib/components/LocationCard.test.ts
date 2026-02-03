import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import LocationCard from './LocationCard.svelte';
import type { Location } from '$lib/services/api';

describe('LocationCard', () => {
	const mockLocation: Location = {
		id: '1',
		name: 'Block A',
		type: 'houseblock',
		building: 'Main',
		floor: 1,
		capacity: 50,
		created_at: '2026-01-27T10:00:00',
		updated_at: '2026-01-27T10:00:00'
	};

	it('should render location hierarchy path', () => {
		render(LocationCard, { props: { location: mockLocation, hierarchyPath: 'Block A' } });
		expect(screen.getByText('Block A')).toBeInTheDocument();
	});

	it('should render location details', () => {
		render(LocationCard, { props: { location: mockLocation, hierarchyPath: 'Block A' } });
		expect(screen.getByText(/Building: Main/i)).toBeInTheDocument();
		expect(screen.getByText(/Floor: 1/i)).toBeInTheDocument();
		expect(screen.getByText(/Capacity: 50/i)).toBeInTheDocument();
	});

	it('should render edit button', () => {
		render(LocationCard, { props: { location: mockLocation, hierarchyPath: 'Block A' } });
		const editButton = screen.getByRole('button', { name: /edit/i });
		expect(editButton).toBeInTheDocument();
	});

	it('should render delete button', () => {
		render(LocationCard, { props: { location: mockLocation, hierarchyPath: 'Block A' } });
		const deleteButton = screen.getByRole('button', { name: /delete/i });
		expect(deleteButton).toBeInTheDocument();
	});

	it('should display icon for houseblock type', () => {
		render(LocationCard, { props: { location: mockLocation, hierarchyPath: 'Block A' } });
		expect(screen.getByText('🏢')).toBeInTheDocument();
	});

	it('should display icon for cell type', () => {
		const cellLocation: Location = {
			...mockLocation,
			name: 'Cell A-101',
			type: 'cell',
			capacity: 1
		};
		render(LocationCard, { props: { location: cellLocation, hierarchyPath: 'Cell A-101' } });
		expect(screen.getByText('🚪')).toBeInTheDocument();
	});

	it('should display icon for yard type', () => {
		const yardLocation: Location = {
			...mockLocation,
			name: 'Yard',
			type: 'yard',
			building: 'Outdoor',
			floor: 0,
			capacity: 100
		};
		render(LocationCard, { props: { location: yardLocation, hierarchyPath: 'Yard' } });
		expect(screen.getByText('🌳')).toBeInTheDocument();
	});

	it('should display full hierarchy path with parent', () => {
		const childLocation: Location = {
			...mockLocation,
			name: 'Cell A-101',
			type: 'cell',
			parent_id: 'parent-1'
		};
		render(LocationCard, {
			props: { location: childLocation, hierarchyPath: 'Block A > Wing A > Cell A-101' }
		});
		expect(screen.getByText('Block A > Wing A > Cell A-101')).toBeInTheDocument();
	});

	it('should display hierarchy path with separator', () => {
		const childLocation: Location = {
			...mockLocation,
			name: 'Cell A-101',
			type: 'cell',
			parent_id: 'parent-1'
		};
		render(LocationCard, {
			props: { location: childLocation, hierarchyPath: 'Block A > Cell A-101' }
		});
		const heading = screen.getByRole('heading', { level: 3 });
		expect(heading.textContent).toContain('>');
	});
});
