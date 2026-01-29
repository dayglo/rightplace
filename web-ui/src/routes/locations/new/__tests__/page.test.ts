import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Page from '../+page.svelte';

describe('Add Location Page', () => {
	it('should render page title', () => {
		render(Page);
		expect(screen.getByText('Add New Location')).toBeInTheDocument();
	});

	it('should render back link', () => {
		render(Page);
		const backLink = screen.getByRole('link', { name: /back/i });
		expect(backLink).toBeInTheDocument();
		expect(backLink).toHaveAttribute('href', '/locations');
	});

	it('should render name input', () => {
		render(Page);
		const nameInput = screen.getByLabelText(/name/i);
		expect(nameInput).toBeInTheDocument();
		expect(nameInput).toHaveAttribute('required');
	});

	it('should render type dropdown', () => {
		render(Page);
		const typeSelect = screen.getByLabelText(/type/i);
		expect(typeSelect).toBeInTheDocument();
		expect(typeSelect).toHaveAttribute('required');
	});

	it('should have type options for block, cell, yard', () => {
		render(Page);
		const typeSelect = screen.getByLabelText(/type/i);
		const options = typeSelect.querySelectorAll('option');
		const optionValues = Array.from(options).map((opt) => opt.getAttribute('value'));
		expect(optionValues).toContain('block');
		expect(optionValues).toContain('cell');
		expect(optionValues).toContain('yard');
	});

	it('should render building input', () => {
		render(Page);
		const buildingInput = screen.getByLabelText(/building/i);
		expect(buildingInput).toBeInTheDocument();
		expect(buildingInput).toHaveAttribute('required');
	});

	it('should render floor input', () => {
		render(Page);
		const floorInput = screen.getByLabelText(/floor/i);
		expect(floorInput).toBeInTheDocument();
		expect(floorInput).toHaveAttribute('type', 'number');
		expect(floorInput).toHaveAttribute('required');
	});

	it('should render capacity input', () => {
		render(Page);
		const capacityInput = screen.getByLabelText(/capacity/i);
		expect(capacityInput).toBeInTheDocument();
		expect(capacityInput).toHaveAttribute('type', 'number');
		expect(capacityInput).toHaveAttribute('required');
	});

	it('should render parent location dropdown (optional)', () => {
		render(Page);
		const parentSelect = screen.getByLabelText(/parent location/i);
		expect(parentSelect).toBeInTheDocument();
		expect(parentSelect).not.toHaveAttribute('required');
	});

	it('should render cancel button', () => {
		render(Page);
		const cancelButton = screen.getByRole('button', { name: /cancel/i });
		expect(cancelButton).toBeInTheDocument();
	});

	it('should render create button', () => {
		render(Page);
		const createButton = screen.getByRole('button', { name: /create location/i });
		expect(createButton).toBeInTheDocument();
		expect(createButton).toHaveAttribute('type', 'submit');
	});

	it('should have form element', () => {
		render(Page);
		const form = document.querySelector('form');
		expect(form).toBeInTheDocument();
	});
});
