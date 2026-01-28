import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import StatCard from './StatCard.svelte';

describe('StatCard', () => {
	it('should render with title and count', () => {
		render(StatCard, {
			props: {
				title: 'Prisoners',
				count: 5,
				href: '/prisoners'
			}
		});

		expect(screen.getByText('Prisoners')).toBeInTheDocument();
		expect(screen.getByText('5')).toBeInTheDocument();
	});

	it('should render with enrolled suffix when provided', () => {
		render(StatCard, {
			props: {
				title: 'Prisoners',
				count: 5,
				suffix: 'enrolled',
				href: '/prisoners'
			}
		});

		expect(screen.getByText('5')).toBeInTheDocument();
		expect(screen.getByText('enrolled')).toBeInTheDocument();
	});

	it('should render link with correct href', () => {
		render(StatCard, {
			props: {
				title: 'Prisoners',
				count: 5,
				href: '/prisoners'
			}
		});

		const link = screen.getByRole('link', { name: /view all/i });
		expect(link).toHaveAttribute('href', '/prisoners');
	});

	it('should render with icon when provided', () => {
		render(StatCard, {
			props: {
				title: 'Prisoners',
				count: 5,
				href: '/prisoners',
				icon: '👤'
			}
		});

		expect(screen.getByText('👤')).toBeInTheDocument();
	});

	it('should handle zero count', () => {
		render(StatCard, {
			props: {
				title: 'Prisoners',
				count: 0,
				href: '/prisoners'
			}
		});

		expect(screen.getByText('0')).toBeInTheDocument();
	});
});
