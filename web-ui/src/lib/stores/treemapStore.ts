/**
 * Treemap store - State management for rollcall treemap visualization
 */
import { writable, derived } from 'svelte/store';

export interface InmateVerification {
	inmate_id: string;
	name: string;
	status: string; // verified, not_found, wrong_location, pending
}

export interface TreemapMetadata {
	inmate_count: number;
	verified_count: number;
	failed_count: number;
	scheduled_time?: string;
	actual_time?: string;
	inmates?: InmateVerification[]; // Prisoner details (for cells)
}

export interface TreemapNode {
	id?: string;
	name: string;
	type: string; // root, prison, houseblock, wing, landing, cell
	value: number;
	status: string; // grey, amber, green, red
	children?: TreemapNode[];
	metadata?: TreemapMetadata;
}

export interface TreemapResponse {
	name: string;
	type: string;
	value: number;
	children: TreemapNode[];
}

// Occupancy mode - how to determine where inmates are
export type OccupancyMode = 'scheduled' | 'home_cell';

interface TreemapState {
	// Selected rollcall IDs (empty = show all)
	selectedRollcallIds: string[];

	// Current timestamp for visualization
	timestamp: Date;

	// Date range for slider
	dateRange: {
		start: Date;
		end: Date;
	};

	// Treemap data
	data: TreemapResponse | null;

	// Loading state
	loading: boolean;

	// Error state
	error: string | null;

	// Live mode (auto-update to current time)
	liveMode: boolean;

	// Include empty locations
	includeEmpty: boolean;

	// Occupancy mode - how to determine where inmates are
	occupancyMode: OccupancyMode;

	// Current zoom path (for breadcrumb navigation)
	zoomPath: TreemapNode[];
}

const initialState: TreemapState = {
	selectedRollcallIds: [],
	timestamp: new Date(),
	dateRange: {
		start: new Date(Date.now() - 24 * 60 * 60 * 1000), // 24 hours ago
		end: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours from now
	},
	data: null,
	loading: false,
	error: null,
	liveMode: false,
	includeEmpty: false,
	occupancyMode: 'home_cell', // Default to home_cell mode until schedule data is populated
	zoomPath: [],
};

function createTreemapStore() {
	const { subscribe, set, update } = writable<TreemapState>(initialState);

	return {
		subscribe,

		// Set selected rollcall IDs
		setRollcalls: (rollcallIds: string[]) => {
			update(state => ({ ...state, selectedRollcallIds: rollcallIds }));
		},

		// Set timestamp
		setTimestamp: (timestamp: Date) => {
			update(state => ({ ...state, timestamp, liveMode: false }));
		},

		// Set date range
		setDateRange: (start: Date, end: Date) => {
			update(state => ({ ...state, dateRange: { start, end } }));
		},

		// Toggle live mode
		toggleLiveMode: () => {
			update(state => {
				const newLiveMode = !state.liveMode;
				return {
					...state,
					liveMode: newLiveMode,
					timestamp: newLiveMode ? new Date() : state.timestamp,
				};
			});
		},

		// Toggle include empty
		toggleIncludeEmpty: () => {
			update(state => ({ ...state, includeEmpty: !state.includeEmpty }));
		},

		// Set occupancy mode
		setOccupancyMode: (mode: OccupancyMode) => {
			update(state => ({ ...state, occupancyMode: mode }));
		},

		// Fetch treemap data
		fetchData: async (baseUrl: string = 'http://localhost:8000') => {
			update(state => ({ ...state, loading: true, error: null }));

			try {
				const state = { ...initialState };
				update(s => {
					state.selectedRollcallIds = s.selectedRollcallIds;
					state.timestamp = s.timestamp;
					state.includeEmpty = s.includeEmpty;
					state.occupancyMode = s.occupancyMode;
					return s;
				});

				// Build query parameters
				const params = new URLSearchParams({
					timestamp: state.timestamp.toISOString(),
					include_empty: state.includeEmpty.toString(),
					occupancy_mode: state.occupancyMode,
				});

				if (state.selectedRollcallIds.length > 0) {
					params.set('rollcall_ids', state.selectedRollcallIds.join(','));
				}

				const response = await fetch(`${baseUrl}/api/v1/treemap?${params}`);

				if (!response.ok) {
					throw new Error(`HTTP ${response.status}: ${response.statusText}`);
				}

				const data = await response.json();

				update(s => ({ ...s, data, loading: false, zoomPath: [] }));
			} catch (err) {
				const errorMessage = err instanceof Error ? err.message : 'Unknown error';
				update(state => ({ ...state, loading: false, error: errorMessage }));
			}
		},

		// Zoom to a node
		zoomTo: (node: TreemapNode) => {
			update(state => {
				// Add node to zoom path if not already there
				const pathIndex = state.zoomPath.findIndex(n => n.id === node.id);
				if (pathIndex >= 0) {
					// Clicked on breadcrumb - zoom back
					return { ...state, zoomPath: state.zoomPath.slice(0, pathIndex + 1) };
				} else {
					// Zoom in
					return { ...state, zoomPath: [...state.zoomPath, node] };
				}
			});
		},

		// Zoom out one level
		zoomOut: () => {
			update(state => {
				if (state.zoomPath.length === 0) return state;
				return { ...state, zoomPath: state.zoomPath.slice(0, -1) };
			});
		},

		// Zoom out to root
		zoomToRoot: () => {
			update(state => ({ ...state, zoomPath: [] }));
		},

		// Reset to initial state
		reset: () => {
			set(initialState);
		},
	};
}

export const treemapStore = createTreemapStore();

// Derived store for current zoom node
export const currentZoomNode = derived(
	treemapStore,
	$store => {
		if ($store.zoomPath.length === 0) return $store.data;
		return $store.zoomPath[$store.zoomPath.length - 1];
	}
);
