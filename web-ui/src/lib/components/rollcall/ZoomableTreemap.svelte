<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import type { TreemapNode } from '$lib/stores/treemapStore';

	export let data: TreemapNode | null = null;
	export let onNodeClick: (node: TreemapNode) => void = () => {};

	let container: HTMLDivElement;
	let width = 1200;
	let height = 800;

	const colorMap: Record<string, string> = {
		grey: '#6B7280',   // gray-500
		amber: '#F59E0B',  // amber-500
		green: '#10B981',  // emerald-500
		red: '#EF4444'     // red-500
	};

	function renderTreemap() {
		if (!container || !data) return;

		// Clear previous render
		d3.select(container).selectAll('*').remove();

		// Create SVG
		const svg = d3.select(container)
			.append('svg')
			.attr('width', width)
			.attr('height', height)
			.attr('class', 'treemap-svg');

		// Create treemap layout
		const root = d3.hierarchy(data)
			.sum(d => d.value || 0)
			.sort((a, b) => (b.value || 0) - (a.value || 0));

		d3.treemap<TreemapNode>()
			.size([width, height])
			.paddingInner(2)
			.paddingOuter(4)
			.round(true)
			(root as any);

		// Create cells
		const cell = svg.selectAll('g')
			.data(root.leaves())
			.join('g')
			.attr('transform', (d: any) => `translate(${d.x0},${d.y0})`);

		// Add rectangles
		cell.append('rect')
			.attr('width', (d: any) => d.x1 - d.x0)
			.attr('height', (d: any) => d.y1 - d.y0)
			.attr('fill', (d: any) => colorMap[d.data.status] || colorMap.grey)
			.attr('stroke', '#fff')
			.attr('stroke-width', 2)
			.attr('class', 'cursor-pointer hover:opacity-80 transition-opacity')
			.on('click', (event: MouseEvent, d: any) => {
				event.stopPropagation();
				onNodeClick(d.data);
			});

		// Add labels
		cell.append('text')
			.attr('x', 4)
			.attr('y', 16)
			.text((d: any) => d.data.name)
			.attr('font-size', '12px')
			.attr('fill', '#fff')
			.attr('font-weight', 'bold')
			.attr('pointer-events', 'none')
			.each(function(d: any) {
				const textWidth = (d.x1 - d.x0) - 8;
				const text = d3.select(this);
				let textContent = d.data.name;

				// Truncate if too long
				if (this.getComputedTextLength() > textWidth) {
					while (this.getComputedTextLength() > textWidth && textContent.length > 0) {
						textContent = textContent.slice(0, -1);
						text.text(textContent + '...');
					}
				}
			});

		// Add metadata (if space allows)
		cell.append('text')
			.attr('x', 4)
			.attr('y', 32)
			.text((d: any) => {
				const meta = d.data.metadata;
				if (!meta) return '';
				if (meta.inmate_count === 0) return 'Empty';
				if (meta.verified_count + meta.failed_count === 0) return `${meta.inmate_count} inmates`;
				return `${meta.verified_count}/${meta.inmate_count} verified`;
			})
			.attr('font-size', '10px')
			.attr('fill', '#fff')
			.attr('opacity', 0.9)
			.attr('pointer-events', 'none')
			.each(function(d: any) {
				const cellHeight = d.y1 - d.y0;
				// Hide if cell too small
				if (cellHeight < 50) {
					d3.select(this).remove();
				}
			});

		// Add tooltip
		const tooltip = d3.select('body')
			.append('div')
			.attr('class', 'treemap-tooltip')
			.style('position', 'absolute')
			.style('background', 'rgba(0, 0, 0, 0.9)')
			.style('color', '#fff')
			.style('padding', '8px 12px')
			.style('border-radius', '4px')
			.style('font-size', '12px')
			.style('pointer-events', 'none')
			.style('opacity', 0)
			.style('z-index', '1000');

		cell.on('mouseenter', (event: MouseEvent, d: any) => {
			const meta = d.data.metadata || {};
			tooltip
				.style('opacity', 1)
				.html(`
					<strong>${d.data.name}</strong><br/>
					Type: ${d.data.type}<br/>
					Status: ${d.data.status}<br/>
					Inmates: ${meta.inmate_count || 0}<br/>
					Verified: ${meta.verified_count || 0}<br/>
					Failed: ${meta.failed_count || 0}
				`);
		})
		.on('mousemove', (event: MouseEvent) => {
			tooltip
				.style('left', (event.pageX + 10) + 'px')
				.style('top', (event.pageY - 10) + 'px');
		})
		.on('mouseleave', () => {
			tooltip.style('opacity', 0);
		});
	}

	onMount(() => {
		// Update dimensions based on container
		if (container) {
			width = container.clientWidth || 1200;
			height = container.clientHeight || 800;
		}
		renderTreemap();

		return () => {
			// Cleanup tooltip
			d3.selectAll('.treemap-tooltip').remove();
		};
	});

	$: if (data) {
		renderTreemap();
	}
</script>

<div bind:this={container} class="treemap-container w-full h-full min-h-[600px]"></div>

<style>
	.treemap-container {
		background: #f3f4f6;
		border-radius: 8px;
		overflow: hidden;
	}

	:global(.treemap-svg) {
		display: block;
	}
</style>
