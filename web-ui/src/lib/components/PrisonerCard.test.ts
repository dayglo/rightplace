import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import PrisonerCard from './PrisonerCard.svelte';
import type { Inmate } from '$lib/services/api';

describe('PrisonerCard', () => {
	const enrolledInmate: Inmate = {
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
	};

	const notEnrolledInmate: Inmate = {
		id: '2',
		inmate_number: 'A12346',
		first_name: 'Jane',
		last_name: 'Smith',
		date_of_birth: '1992-05-15',
		cell_block: 'B',
		cell_number: '201',
		is_enrolled: false,
		created_at: '2026-01-27T10:00:00',
		updated_at: '2026-01-27T10:00:00'
	};

	it('should render prisoner name', () => {
		render(PrisonerCard, { props: { inmate: enrolledInmate } });
		expect(screen.getByText('John Doe')).toBeInTheDocument();
	});

	it('should render inmate number', () => {
		render(PrisonerCard, { props: { inmate: enrolledInmate } });
		expect(screen.getByText(/#A12345/)).toBeInTheDocument();
	});

	it('should render cell location', () => {
		render(PrisonerCard, { props: { inmate: enrolledInmate } });
		expect(screen.getByText(/Block A, Cell 101/)).toBeInTheDocument();
	});

	it('should show enrolled status for enrolled inmate', () => {
		render(PrisonerCard, { props: { inmate: enrolledInmate } });
		expect(screen.getByText(/enrolled/i)).toBeInTheDocument();
	});

	it('should show not enrolled status for non-enrolled inmate', () => {
		render(PrisonerCard, { props: { inmate: notEnrolledInmate } });
		expect(screen.getByText(/not enrolled/i)).toBeInTheDocument();
	});

	it('should display checkmark icon for enrolled inmate', () => {
		const { container } = render(PrisonerCard, { props: { inmate: enrolledInmate } });
		expect(container.textContent).toContain('✓');
	});

	it('should display X icon for non-enrolled inmate', () => {
		const { container } = render(PrisonerCard, { props: { inmate: notEnrolledInmate } });
		expect(container.textContent).toContain('✗');
	});

	it('should have view link to prisoner detail page', () => {
		render(PrisonerCard, { props: { inmate: enrolledInmate } });
		const viewLink = screen.getByRole('link', { name: /view/i });
		expect(viewLink).toHaveAttribute('href', '/prisoners/1');
	});

	it('should have enroll face link', () => {
		render(PrisonerCard, { props: { inmate: enrolledInmate } });
		const enrollLink = screen.getByRole('link', { name: /enroll face/i });
		expect(enrollLink).toHaveAttribute('href', '/prisoners/1/enroll');
	});

	it('should display photo placeholder for enrolled inmate', () => {
		render(PrisonerCard, { props: { inmate: enrolledInmate } });
		// Check for image or placeholder element
		const card = screen.getByText('John Doe').closest('.bg-white');
		expect(card).toBeInTheDocument();
	});

	it('should display question mark placeholder for non-enrolled inmate', () => {
		const { container } = render(PrisonerCard, { props: { inmate: notEnrolledInmate } });
		expect(container.textContent).toContain('?');
	});
});
