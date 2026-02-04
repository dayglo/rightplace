/**
 * Tests for the CirclePacking visualization component
 *
 * Note: Full D3 visualization testing is complex and better done manually.
 * These tests verify basic component structure and imports.
 *
 * For comprehensive testing of the manual zoom controls, see:
 * docs/manual-zoom-controls-testing.md
 */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import '@testing-library/jest-dom';
import CirclePacking from './CirclePacking.svelte';

describe('CirclePacking Component', () => {
	it('should import and render without errors', () => {
		// Render with null data (should handle gracefully)
		const { container } = render(CirclePacking, {
			props: {
				data: null,
				onNodeClick: () => {},
				onZoomOut: () => {}
			}
		});

		// Container should be rendered
		const packingContainer = container.querySelector('.circle-packing-container');
		expect(packingContainer).toBeTruthy();
	});

	it('should have manual zoom control buttons in the DOM', () => {
		const { container } = render(CirclePacking, {
			props: {
				data: null,
				onNodeClick: () => {},
				onZoomOut: () => {}
			}
		});

		// Manual zoom controls should be in the DOM
		const buttons = container.querySelectorAll('button');
		// Should have at least the zoom controls (may not be visible without data)
		expect(buttons.length).toBeGreaterThanOrEqual(2);
	});
});
