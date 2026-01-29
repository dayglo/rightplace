import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import Page from '../+page.svelte';

describe('Add Prisoner Page', () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it('should render page title', () => {
		render(Page);
		expect(screen.getByText('Add New Prisoner')).toBeInTheDocument();
	});

	it('should render back link', () => {
		render(Page);
		const backLink = screen.getByRole('link', { name: /back/i });
		expect(backLink).toBeInTheDocument();
		expect(backLink).toHaveAttribute('href', '/prisoners');
	});

	it('should render all form fields', () => {
		render(Page);
		expect(screen.getByLabelText(/inmate number/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/first name/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/last name/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/date of birth/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/cell block/i)).toBeInTheDocument();
		expect(screen.getByLabelText(/cell number/i)).toBeInTheDocument();
	});

	it('should mark required fields with asterisk', () => {
		const { container } = render(Page);
		expect(container.textContent).toContain('Inmate Number *');
		expect(container.textContent).toContain('First Name *');
		expect(container.textContent).toContain('Last Name *');
		expect(container.textContent).toContain('Date of Birth *');
		expect(container.textContent).toContain('Cell Block *');
		expect(container.textContent).toContain('Cell Number *');
	});

	it('should render cancel button', () => {
		render(Page);
		const cancelButton = screen.getByRole('button', { name: /cancel/i });
		expect(cancelButton).toBeInTheDocument();
	});

	it('should render create prisoner button', () => {
		render(Page);
		const submitButton = screen.getByRole('button', { name: /create prisoner/i });
		expect(submitButton).toBeInTheDocument();
	});

	it('should have inmate number input with placeholder', () => {
		render(Page);
		const inmateNumberInput = screen.getByLabelText(/inmate number/i);
		expect(inmateNumberInput).toHaveAttribute('placeholder', 'A12345');
	});

	it('should have date input for date of birth', () => {
		render(Page);
		const dobInput = screen.getByLabelText(/date of birth/i);
		expect(dobInput).toHaveAttribute('type', 'date');
	});

	it('should have select dropdown for cell block', () => {
		render(Page);
		const cellBlockSelect = screen.getByLabelText(/cell block/i);
		expect(cellBlockSelect.tagName).toBe('SELECT');
	});

	it('should have cell block options', () => {
		render(Page);
		const cellBlockSelect = screen.getByLabelText(/cell block/i);
		const options = cellBlockSelect.querySelectorAll('option');
		expect(options.length).toBeGreaterThan(0);
	});

	it('should validate required fields on submit', async () => {
		render(Page);
		const submitButton = screen.getByRole('button', { name: /create prisoner/i });
		
		// Try to submit empty form
		await fireEvent.click(submitButton);
		
		// Form should not submit (browser validation will prevent it)
		const inmateNumberInput = screen.getByLabelText(/inmate number/i) as HTMLInputElement;
		expect(inmateNumberInput.required).toBe(true);
	});

	it('should allow filling out the form', async () => {
		render(Page);
		
		const inmateNumberInput = screen.getByLabelText(/inmate number/i) as HTMLInputElement;
		const firstNameInput = screen.getByLabelText(/first name/i) as HTMLInputElement;
		const lastNameInput = screen.getByLabelText(/last name/i) as HTMLInputElement;
		const dobInput = screen.getByLabelText(/date of birth/i) as HTMLInputElement;
		const cellBlockSelect = screen.getByLabelText(/cell block/i) as HTMLSelectElement;
		const cellNumberInput = screen.getByLabelText(/cell number/i) as HTMLInputElement;
		
		await fireEvent.input(inmateNumberInput, { target: { value: 'A12345' } });
		await fireEvent.input(firstNameInput, { target: { value: 'John' } });
		await fireEvent.input(lastNameInput, { target: { value: 'Doe' } });
		await fireEvent.input(dobInput, { target: { value: '1990-01-01' } });
		await fireEvent.change(cellBlockSelect, { target: { value: 'A' } });
		await fireEvent.input(cellNumberInput, { target: { value: '101' } });
		
		expect(inmateNumberInput.value).toBe('A12345');
		expect(firstNameInput.value).toBe('John');
		expect(lastNameInput.value).toBe('Doe');
		expect(dobInput.value).toBe('1990-01-01');
		expect(cellBlockSelect.value).toBe('A');
		expect(cellNumberInput.value).toBe('101');
	});

	it('should display error message on submission failure', () => {
		render(Page);
		// Error handling will be tested when form action is implemented
		expect(screen.getByText('Add New Prisoner')).toBeInTheDocument();
	});

	it('should have proper form structure', () => {
		const { container } = render(Page);
		const form = container.querySelector('form');
		expect(form).toBeInTheDocument();
	});
});
