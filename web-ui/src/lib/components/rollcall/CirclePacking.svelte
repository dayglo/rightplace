<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';
	import type { TreemapNode } from '$lib/stores/treemapStore';
	import { treemapStore } from '$lib/stores/treemapStore';

	export let data: TreemapNode | null = null;
	export let onNodeClick: (node: TreemapNode) => void = () => {};
	export let onZoomOut: () => void = () => {};

	let container: HTMLDivElement;
	let width = 1200;
	let height = 800;
	let canZoomOut = false;
	let focus: any = null;
	let view: [number, number, number] = [0, 0, 0];
	let root: any = null; // Will hold hierarchy root (needed for zoom limits)
	let handleManualZoomFn: ((direction: 'in' | 'out') => void) | null = null;
	let zoomFn: ((d: any, event?: MouseEvent) => void) | null = null;

	// Update canZoomOut based on focus
	$: canZoomOut = focus && focus.parent;

	// Computed values for manual zoom button states
	$: canZoomIn = focus && view[2] > focus.r * 1.5;
	$: canZoomOut_manual = root && view[2] < root.r * 2.6;

	const colorMap: Record<string, string> = {
		grey: '#6B7280',   // gray-500
		amber: '#F59E0B',  // amber-500
		green: '#10B981',  // emerald-500
		red: '#EF4444'     // red-500
	};

	function renderCirclePacking() {
		if (!container || !data) return;

		// Clear previous render and cleanup tooltips
		d3.select(container).selectAll('*').remove();
		d3.selectAll('.circle-packing-tooltip').remove();

		// Local variables to store references needed by zoom controls
		let svg: any;
		let node: any;
		let label: any;

		// Create SVG with centered viewBox
		svg = d3.select(container)
			.append('svg')
			.attr('viewBox', `-${width / 2} -${height / 2} ${width} ${height}`)
			.attr('width', width)
			.attr('height', height)
			.attr('class', 'circle-packing-svg')
			.style('display', 'block')
			.style('cursor', 'pointer')
			.on('click', (event: MouseEvent) => {
				// Only zoom out if clicking on background (not on circles)
				if (event.target === event.currentTarget && focus.parent) {
					zoom(focus.parent, event);
				}
			});

		// Create hierarchy and pack layout
		root = d3.hierarchy(data)
			.sum(d => d.value || 0)
			.sort((a, b) => (b.value || 0) - (a.value || 0));

		const pack = d3.pack<TreemapNode>()
			.size([width, height])
			.padding(1);

		pack(root as any);

		// Initialize focus and view
		focus = root;
		view = [focus.x, focus.y, focus.r * 2.6];

		// Helper function to zoom to a specific view
		function zoomTo(v: [number, number, number]) {
			const k = width / v[2];
			view = v;

			if (label) label.attr('transform', (d: any) => `translate(${(d.x - v[0]) * k},${(d.y - v[1]) * k})`);
			if (node) {
				node.attr('transform', (d: any) => `translate(${(d.x - v[0]) * k},${(d.y - v[1]) * k})`);
				node.attr('r', (d: any) => d.r * k);
			}
		}

		// Zoom function with smooth transition
		function zoom(d: any, event?: MouseEvent) {
			const focus0 = focus;
			focus = d;

			// Determine duration (longer with alt key)
			const duration = event?.altKey ? 7500 : 750;

			const transition = svg.transition()
				.duration(duration)
				.tween('zoom', () => {
					const i = d3.interpolateZoom(view, [focus.x, focus.y, focus.r * 2.6]);
					return (t: number) => zoomTo(i(t));
				});

			// Update label visibility with transition
			label
				.filter(function(this: any, d: any) {
					return d.parent === focus || this.style.display === 'inline';
				})
				.transition(transition as any)
				.style('fill-opacity', (d: any) => d.parent === focus ? 1 : 0)
				.style('stroke-opacity', (d: any) => d.parent === focus ? 1 : 0)
				.on('start', function(this: any, d: any) {
					if (d.parent === focus) this.style.display = 'inline';
				})
				.on('end', function(this: any, d: any) {
					if (d.parent !== focus) this.style.display = 'none';
				});
		}

		// Manual zoom function
		function handleManualZoom(direction: 'in' | 'out') {
			if (!focus || !svg) return;

			// Calculate new diameter
			const zoomFactor = direction === 'in' ? 0.8 : 1.25; // 20% change
			let newDiameter = view[2] * zoomFactor;

			// Clamp to limits
			const minDiameter = focus.r * 1.5;
			const maxDiameter = root.r * 2.6;
			newDiameter = Math.max(minDiameter, Math.min(maxDiameter, newDiameter));

			// Keep same center, change diameter
			const newView: [number, number, number] = [view[0], view[1], newDiameter];

			// Animate the zoom
			svg.transition()
				.duration(300)
				.tween('zoom', () => {
					const i = d3.interpolateZoom(view, newView);
					return (t: number) => zoomTo(i(t));
				});
		}

		// Create tooltip first so we can reference it in event handlers
		const tooltip = d3.select('body')
			.append('div')
			.attr('class', 'circle-packing-tooltip')
			.style('position', 'absolute')
			.style('background', 'rgba(0, 0, 0, 0.9)')
			.style('color', '#fff')
			.style('padding', '8px 12px')
			.style('border-radius', '4px')
			.style('font-size', '12px')
			.style('pointer-events', 'none')
			.style('opacity', 0)
			.style('z-index', '1000');

		// Create container groups for circles and labels
		const nodeGroup = svg.append('g');
		const labelGroup = svg.append('g')
			.style('font', '10px sans-serif')
			.attr('pointer-events', 'none')
			.attr('text-anchor', 'middle');

		// Create circles for all nodes (skip root)
		node = nodeGroup.selectAll('circle')
			.data(root.descendants().slice(1))
			.join('circle')
			.attr('r', (d: any) => d.r)
			.attr('fill', (d: any) => {
				// Use the node's own status if it has one, otherwise inherit from parent
				const status = d.data.status || 'grey';
				return colorMap[status] || colorMap.grey;
			})
			.attr('stroke', '#fff')
			.attr('stroke-width', 2)
			.attr('opacity', (d: any) => d.children ? 0.3 : 0.8)
			.attr('class', 'cursor-pointer hover:opacity-100 transition-opacity')
			.on('click', (event: MouseEvent, d: any) => {
				event.stopPropagation();
				tooltip.style('opacity', 0); // Hide tooltip on click
				if (focus !== d) {
					zoom(d, event);
				}
			});

		// Create labels for all nodes
		label = labelGroup.selectAll('text')
			.data(root.descendants())
			.join('text')
			.attr('text-anchor', 'middle')
			.style('fill-opacity', (d: any) => d.parent === root ? 1 : 0)
			.style('display', (d: any) => d.parent === root ? 'inline' : 'none')
			.attr('dy', (d: any) => {
				// Position prison labels at the very top
				if (d.data.type === 'prison') {
					return -d.r + 25; // At the top of the circle
				}
				// Position houseblock labels near the top (but lower than prison)
				if (d.data.type === 'houseblock') {
					return -d.r + 40; // Move down a bit more
				}
				// Position wing labels near the top
				if (d.data.type === 'wing') {
					return -d.r + 20; // Near the top
				}
				// Position landing labels a bit further down
				if (d.data.type === 'landing') {
					return -d.r + 35; // Further down than wing
				}
				return '0.3em'; // Center for other types
			})
			.text((d: any) => {
				// Only show label if circle is large enough
				if (d.r < 20) return '';
				// Don't render the root/current level label (we have it in top right)
				if (d.depth === 0) return '';
				return d.data.name;
			})
			.attr('font-size', (d: any) => {
				// Largest font for prison
				if (d.data.type === 'prison') {
					return Math.min(d.r / 3, 24) + 'px';
				}
				// Larger font for houseblock and wing
				if (d.data.type === 'houseblock' || d.data.type === 'wing') {
					return Math.min(d.r / 4, 18) + 'px';
				}
				// Even larger font for landing (60 inmates, needs to be prominent)
				if (d.data.type === 'landing') {
					return Math.min(d.r / 3, 20) + 'px';
				}
				return Math.min(d.r / 3, 14) + 'px';
			})
			.attr('fill', (d: any) => {
				// Black text with white outline for prison, houseblock, wing, and landing; white for others
				if (d.data.type === 'prison' || d.data.type === 'houseblock' || d.data.type === 'wing' || d.data.type === 'landing') {
					return '#000';
				}
				return '#fff';
			})
			.attr('font-weight', (d: any) => {
				// Bold for all hierarchy levels
				return 'bold';
			})
			.attr('stroke', (d: any) => {
				// White outline for prison, houseblock, wing, and landing
				if (d.data.type === 'prison' || d.data.type === 'houseblock' || d.data.type === 'wing' || d.data.type === 'landing') {
					return '#fff';
				}
				return 'none';
			})
			.attr('stroke-width', (d: any) => {
				// Thicker outline for prison
				if (d.data.type === 'prison') {
					return '4px';
				}
				if (d.data.type === 'houseblock' || d.data.type === 'wing' || d.data.type === 'landing') {
					return '3px';
				}
				return '0';
			})
			.attr('paint-order', 'stroke')
			.attr('pointer-events', 'none')
			.each(function(d: any) {
				const text = d3.select(this);
				const textContent = d.data.name;
				const maxWidth = d.r * 1.8;

				// Truncate if too long
				if (this.getComputedTextLength() > maxWidth) {
					let truncated = textContent;
					while (this.getComputedTextLength() > maxWidth && truncated.length > 0) {
						truncated = truncated.slice(0, -1);
						text.text(truncated + '...');
					}
				}
			});

		// Add tooltip event handlers to nodes
		node.on('mouseenter', (event: MouseEvent, d: any) => {
			const meta = d.data.metadata || {};

			// Build tooltip HTML
			let tooltipHtml = `
				<strong>${d.data.name}</strong><br/>
				Type: ${d.data.type}<br/>
				Status: ${d.data.status}<br/>
				Inmates: ${meta.inmate_count || 0}<br/>
				Verified: ${meta.verified_count || 0}<br/>
				Failed: ${meta.failed_count || 0}
			`;

			// If this is a cell with prisoner details, show them
			if (d.data.type === 'cell' && meta.inmates && meta.inmates.length > 0) {
				tooltipHtml += '<br/><br/><strong>Prisoners:</strong><br/>';
				meta.inmates.forEach((inmate: any) => {
					const statusIcon = inmate.status === 'verified' ? '✓' :
					                   inmate.status === 'not_found' ? '✗' :
					                   inmate.status === 'wrong_location' ? '⚠' : '○';
					const statusColor = inmate.status === 'verified' ? '#10B981' :
					                    inmate.status === 'not_found' ? '#EF4444' :
					                    inmate.status === 'wrong_location' ? '#F59E0B' : '#6B7280';
					tooltipHtml += `<span style="color: ${statusColor}">${statusIcon}</span> ${inmate.name}<br/>`;
				});
			}

			tooltip
				.style('opacity', 1)
				.html(tooltipHtml);
		})
		.on('mousemove', (event: MouseEvent) => {
			tooltip
				.style('left', (event.pageX + 10) + 'px')
				.style('top', (event.pageY - 10) + 'px');
		})
		.on('mouseleave', () => {
			tooltip.style('opacity', 0);
		});

		// Initialize zoom to root
		zoomTo([root.x, root.y, root.r * 2.6]);

		// Expose functions to component template
		handleManualZoomFn = handleManualZoom;
		zoomFn = zoom;
	}

	function handleZoomOutInternal() {
		if (focus && focus.parent && zoomFn) {
			zoomFn(focus.parent);
		}
	}

	onMount(() => {
		// Update dimensions based on container
		if (container) {
			width = container.clientWidth || 1200;
			height = container.clientHeight || 800;
		}
		renderCirclePacking();

		return () => {
			// Cleanup tooltip
			d3.selectAll('.circle-packing-tooltip').remove();
		};
	});

	$: if (data) {
		renderCirclePacking();
	}
</script>

<div class="relative w-full h-full min-h-[600px]">
	<!-- Zoom Out Button -->
	{#if canZoomOut}
		<button
			on:click={handleZoomOutInternal}
			class="absolute top-4 left-4 z-10 px-3 py-2 bg-white hover:bg-gray-100 border border-gray-300 rounded-lg shadow-md text-sm font-medium text-gray-700 transition-colors"
		>
			← Zoom Out
		</button>
	{/if}

	<!-- Current Location Indicator -->
	{#if focus && focus.data}
		<div class="absolute top-4 right-4 z-10 px-3 py-2 bg-white border border-gray-300 rounded-lg shadow-md">
			<div class="text-xs text-gray-500 uppercase tracking-wide">Current View</div>
			<div class="text-sm font-semibold text-gray-900">{focus.data.name}</div>
		</div>
	{/if}

	<!-- Manual Zoom Controls -->
	<div class="absolute bottom-4 right-4 z-10 flex flex-col gap-2">
		<button
			on:click={() => handleManualZoomFn && handleManualZoomFn('in')}
			disabled={!canZoomIn}
			class="w-10 h-10 bg-white hover:bg-gray-100 border border-gray-300 rounded-lg shadow-md text-lg font-bold text-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
			title="Zoom In"
		>
			+
		</button>
		<button
			on:click={() => handleManualZoomFn && handleManualZoomFn('out')}
			disabled={!canZoomOut_manual}
			class="w-10 h-10 bg-white hover:bg-gray-100 border border-gray-300 rounded-lg shadow-md text-lg font-bold text-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
			title="Zoom Out"
		>
			−
		</button>
	</div>

	<div bind:this={container} class="circle-packing-container w-full h-full"></div>
</div>

<style>
	.circle-packing-container {
		background: #f3f4f6;
		border-radius: 8px;
		overflow: hidden;
	}

	:global(.circle-packing-svg) {
		display: block;
		cursor: pointer;
	}
</style>
