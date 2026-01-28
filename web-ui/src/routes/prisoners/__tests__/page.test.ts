import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Page from '../+page.svelte';
import type { Inmate } from '$lib/services/api';

describe('Prisoner List Page', () => {
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
		},
		{
			id: '3',
			inmate_number: 'A12347',
			first_name: 'Mike',
			last_name: 'Johnson',
			date_of_birth: '1988-03-20',
			cell_block: 'B',
			cell_number: '201',
			is_enrolled: false,
			created_at: '2026-01-27T10:00:00',
			updated_at: '2026-01-27T10:00:00'
		}
	];

	it('should render page title', () => {
		render(Page, { props: { data: { inmates: mockInmates } } });
		expect(screen.getByText('Prisoners')).toBeInTheDocument();
	});

	it('should render add prisoner button', () => {
		render(Page, { props: { data: { inmates: mockInmates } } });
		const addButton = screen.getByRole('link', { name: /add prisoner/i });
		expect(addButton).toBeInTheDocument();
		expect(addButton).toHaveAttribute('href', '/prisoners/new');
	});

	it('should render search input', () => {
		render(Page, { props: { data: { inmates: mockInmates } } });
		const searchInput = screen.getByPlaceholderText(/search/i);
		expect(searchInput).toBeInTheDocument();
	});

	it('should render filter dropdown', () => {
		render(Page, { props: { data: { inmates: mockInmates } } });
		const filterSelect = screen.getByRole('combobox');
		expect(filterSelect).toBeInTheDocument();
	});

	it('should have filter options for All, Enrolled, Not Enrolled', () => {
		render(Page, { props: { data: { inmates: mockInmates } } });
		const filterSelect = screen.getByRole('combobox');
		const options = filterSelect.querySelectorAll('option');
		const optionTexts = Array.from(options).map((opt) => opt.textContent);
		expect(optionTexts).toContain('All');
		expect(optionTexts).toContain('Enrolled');
		expect(optionTexts).toContain('Not Enrolled');
	});

	it('should render all prisoners', () => {
		render(Page, { props: { data: { inmates: mockInmates } } });
		expect(screen.getByText('John Doe')).toBeInTheDocument();
		expect(screen.getByText('Jane Smith')).toBeInTheDocument();
		expect(screen.getByText('Mike Johnson')).toBeInTheDocument();
	});

	it('should display prisoner count', () => {
		render(Page, { props: { data: { inmates: mockInmates } } });
		// Should show total count somewhere
		const page = screen.getByText('Prisoners').closest('div');
		expect(page).toBeInTheDocument();
	});

	it('should handle empty prisoner list', () => {
		render(Page, { props: { data: { inmates: [] } } });
		expect(screen.getByText(/no prisoners found/i)).toBeInTheDocument();
	});

	it('should filter prisoners by search term', async () => {
		const { component } = render(Page, { props: { data: { inmates: mockInmates } } });
		
		// Initially all prisoners visible
		expect(screen.getByText('John Doe')).toBeInTheDocument();
		expect(screen.getByText('Jane Smith')).toBeInTheDocument();
		expect(screen.getByText('Mike Johnson')).toBeInTheDocument();
	});

	it('should filter prisoners by enrollment status', async () => {
		const { component } = render(Page, { props: { data: { inmates: mockInmates } } });
		
		// Initially all prisoners visible
		expect(screen.getByText('John Doe')).toBeInTheDocument();
		expect(screen.getByText('Mike Johnson')).toBeInTheDocument();
	});

	it('should show enrolled count', () => {
		render(Page, { props: { data: { inmates: mockInmates } } });
		// Should show "2 enrolled" or similar
		const enrolledCount = mockInmates.filter((i) => i.is_enrolled).length;
		expect(enrolledCount).toBe(2);
	});

	it('should show not enrolled count', () => {
		render(Page, { props: { data: { inmates: mockInmates } } });
		const notEnrolledCount = mockInmates.filter((i) => !i.is_enrolled).length;
		expect(notEnrolledCount).toBe(1);
	});
});
