import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import Page from '../+page.svelte';

// Mock the api module
vi.mock('$lib/services/api', () => ({
	updateLocation: vi.fn(),
	getLocations: vi.fn().mockResolvedValue([
		{ id: 'loc-1', name: 'Block A', type: 'houseblock' },
		{ id: 'loc-2', name: 'Wing 1', type: 'wing' }
	])
}));

const mockLocation = {
	id: 'loc-123',
	name: 'Block A',
	type: 'houseblock',
	building: 'Main',
	floor: 1,
	capacity: 50,
	parent_id: undefined,
	created_at: '2024-01-01T00:00:00Z',
	updated_at: '2024-01-01T00:00:00Z'
};

describe('Edit Location Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('should render page title', () => {
		render(Page, { props: { data: { location: mockLocation } } });
		expect(screen.getByText('Edit Location')).toBeInTheDocument();
	});

	it('should render back link', () => {
		render(Page, { props: { data: { location: mockLocation } } });
		const backLink = screen.getByRole('link', { name: /back/i });
		expect(backLink).toBeInTheDocument();
		expect(backLink).toHaveAttribute('href', '/locations');
	});

	it('should render name input with existing value', () => {
		render(Page, { props: { data: { location: mockLocation } } });
		const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement;
		expect(nameInput).toBeInTheDocument();
		expect(nameInput).toHaveAttribute('required');
		expect(nameInput.value).toBe('Block A');
	});

	it('should render type dropdown with existing value', () => {
		render(Page, { props: { data: { location: mockLocation } } });
		const typeSelect = screen.getByLabelText(/type/i) as HTMLSelectElement;
		expect(typeSelect).toBeInTheDocument();
		expect(typeSelect).toHaveAttribute('required');
		expect(typeSelect.value).toBe('houseblock');
	});

	it('should have type options for houseblock, cell, yard', () => {
		render(Page, { props: { data: { location: mockLocation } } });
		const typeSelect = screen.getByLabelText(/type/i);
		const options = typeSelect.querySelectorAll('option');
		const optionValues = Array.from(options).map((opt) => opt.getAttribute('value'));
		expect(optionValues).toContain('houseblock');
		expect(optionValues).toContain('cell');
		expect(optionValues).toContain('yard');
	});

	it('should render building input with existing value', () => {
		render(Page, { props: { data: { location: mockLocation } } });
		const buildingInput = screen.getByLabelText(/building/i) as HTMLInputElement;
		expect(buildingInput).toBeInTheDocument();
		expect(buildingInput).toHaveAttribute('required');
		expect(buildingInput.value).toBe('Main');
	});

	it('should render floor input with existing value', () => {
		render(Page, { props: { data: { location: mockLocation } } });
		const floorInput = screen.getByLabelText(/floor/i) as HTMLInputElement;
		expect(floorInput).toBeInTheDocument();
		expect(floorInput).toHaveAttribute('type', 'number');
		expect(floorInput).toHaveAttribute('required');
		expect(floorInput.value).toBe('1');
	});

	it('should render capacity input with existing value', () => {
		render(Page, { props: { data: { location: mockLocation } } });
		const capacityInput = screen.getByLabelText(/capacity/i) as HTMLInputElement;
		expect(capacityInput).toBeInTheDocument();
		expect(capacityInput).toHaveAttribute('type', 'number');
		expect(capacityInput).toHaveAttribute('required');
		expect(capacityInput.value).toBe('50');
	});

	it('should render parent location dropdown (optional)', () => {
		render(Page, { props: { data: { location: mockLocation } } });
		const parentSelect = screen.getByLabelText(/parent location/i);
		expect(parentSelect).toBeInTheDocument();
		expect(parentSelect).not.toHaveAttribute('required');
	});

	it('should render cancel button', () => {
		render(Page, { props: { data: { location: mockLocation } } });
		const cancelButton = screen.getByRole('button', { name: /cancel/i });
		expect(cancelButton).toBeInTheDocument();
	});

	it('should render save button instead of create', () => {
		render(Page, { props: { data: { location: mockLocation } } });
		const saveButton = screen.getByRole('button', { name: /save changes/i });
		expect(saveButton).toBeInTheDocument();
		expect(saveButton).toHaveAttribute('type', 'submit');
	});

	it('should have form element', () => {
		render(Page, { props: { data: { location: mockLocation } } });
		const form = document.querySelector('form');
		expect(form).toBeInTheDocument();
	});

	it('should show location with parent_id pre-selected', async () => {
		const locationWithParent = {
			...mockLocation,
			parent_id: 'loc-1'
		};
		render(Page, { props: { data: { location: locationWithParent } } });

		// Wait for onMount to complete and options to load
		await waitFor(() => {
			const parentSelect = screen.getByLabelText(/parent location/i) as HTMLSelectElement;
			expect(parentSelect.value).toBe('loc-1');
		});
	});
});
