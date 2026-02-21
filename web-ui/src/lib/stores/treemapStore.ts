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

// Timeline range presets
export type DateRangePreset = '1h' | '24h' | '7d';

// Cache status
export type CacheStatus = 'idle' | 'loading' | 'ready' | 'error';

// Prison info for selection
export interface PrisonInfo {
	id: string;
	name: string;
}

// Rollcall info for selection
export interface RollCallInfo {
	id: string;
	name: string;
	status: string;
	scheduled_at: string;
	started_at: string | null;
	completed_at: string | null;
}

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

	// Filter to only show locations in rollcall routes
	filterToRoute: boolean;

	// Occupancy mode - how to determine where inmates are
	occupancyMode: OccupancyMode;

	// Current zoom path (for breadcrumb navigation)
	zoomPath: TreemapNode[];

	// Prison selection
	availablePrisons: PrisonInfo[];
	selectedPrisonIds: string[];

	// Rollcall selection
	availableRollcalls: RollCallInfo[];
	rollcallsLoading: boolean;

	// Playback state
	isPlaying: boolean;
	playbackSpeed: number; // milliseconds between frames
	playbackStepSeconds: number; // simulation seconds per tick (0 = realtime)

	// Cache configuration
	cacheRangeHours: number;
	cacheStepMinutes: number;

	// Cache state
	timestampCache: Map<string, TreemapResponse>;
	cacheStatus: CacheStatus;
	cacheProgress: number;
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
	filterToRoute: true, // Default to filtering to only show locations in rollcall routes
	occupancyMode: 'home_cell', // Default to home_cell mode until schedule data is populated
	zoomPath: [],
	availablePrisons: [],
	selectedPrisonIds: [],
	availableRollcalls: [],
	rollcallsLoading: false,
	isPlaying: false,
	playbackSpeed: 3000, // 3 seconds between frames to allow API response time
	playbackStepSeconds: 60, // 1 minute per tick by default
	cacheRangeHours: 12,
	cacheStepMinutes: 15,
	timestampCache: new Map(),
	cacheStatus: 'idle',
	cacheProgress: 0,
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

		// Toggle filter to route
		toggleFilterToRoute: () => {
			update(state => ({ ...state, filterToRoute: !state.filterToRoute }));
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
					state.filterToRoute = s.filterToRoute;
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
					// Only filter to route when rollcalls are selected
					if (state.filterToRoute) {
						params.set('filter_to_route', 'true');
					}
				}

				const response = await fetch(`${baseUrl}/api/v1/treemap?${params}`);

				if (!response.ok) {
					throw new Error(`HTTP ${response.status}: ${response.statusText}`);
				}

				const data = await response.json();

				// Preserve zoom path so users can watch cells change color during playback
				update(s => ({ ...s, data, loading: false }));
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

		// Fetch available prisons
		fetchPrisons: async (baseUrl: string = 'http://localhost:8000') => {
			try {
				const response = await fetch(`${baseUrl}/api/v1/locations?type=prison`);
				if (!response.ok) throw new Error('Failed to fetch prisons');
				const prisons = await response.json();
				const prisonInfos: PrisonInfo[] = prisons.map((p: any) => ({ id: p.id, name: p.name }));
				update(state => ({
					...state,
					availablePrisons: prisonInfos,
					selectedPrisonIds: prisonInfos.length > 0 ? [prisonInfos[0].id] : [],
				}));
			} catch (err) {
				console.error('Failed to fetch prisons:', err);
			}
		},

		// Fetch available rollcalls
		fetchRollcalls: async (baseUrl: string = 'http://localhost:8000') => {
			update(state => ({ ...state, rollcallsLoading: true }));
			try {
				let currentTimestamp: Date = new Date();
				update(s => { currentTimestamp = s.timestamp; return s; });

				// Fetch all rollcalls
				const response = await fetch(`${baseUrl}/api/v1/rollcalls?limit=200`);
				if (!response.ok) throw new Error('Failed to fetch rollcalls');
				const rollcalls = await response.json();

				// Filter to show only rollcalls active at the selected timestamp
				const filteredRollcalls = rollcalls.filter((rc: any) => {
					const scheduledAt = new Date(rc.scheduled_at);
					const completedAt = rc.completed_at ? new Date(rc.completed_at) : null;
					const startedAt = rc.started_at ? new Date(rc.started_at) : null;

					// Include if:
					// - Scheduled at or before timestamp AND (not completed OR completed after timestamp)
					// - Or if in_progress/scheduled and within 24h window
					if (completedAt) {
						return scheduledAt <= currentTimestamp && completedAt >= currentTimestamp;
					} else if (startedAt) {
						return startedAt <= currentTimestamp;
					} else {
						// Scheduled but not started - show if within 24h window
						const timeDiff = Math.abs(currentTimestamp.getTime() - scheduledAt.getTime());
						return timeDiff < 24 * 60 * 60 * 1000;
					}
				});

				const rollcallInfos: RollCallInfo[] = filteredRollcalls.map((rc: any) => ({
					id: rc.id,
					name: rc.name,
					status: rc.status,
					scheduled_at: rc.scheduled_at,
					started_at: rc.started_at,
					completed_at: rc.completed_at,
				}));
				update(state => ({
					...state,
					availableRollcalls: rollcallInfos,
					rollcallsLoading: false,
				}));
			} catch (err) {
				console.error('Failed to fetch rollcalls:', err);
				update(state => ({ ...state, rollcallsLoading: false }));
			}
		},

		// Set selected prisons
		setSelectedPrisons: (prisonIds: string[]) => {
			update(state => ({ ...state, selectedPrisonIds: prisonIds }));
		},

		// Toggle playback
		togglePlayback: () => {
			update(state => ({ ...state, isPlaying: !state.isPlaying }));
		},

		// Set playback step duration (seconds per tick, 0 = realtime)
		setPlaybackStep: (seconds: number) => {
			update(state => ({ ...state, playbackStepSeconds: seconds }));
		},

		// Step forward by minutes
		stepForward: (minutes: number = 15) => {
			update(state => ({
				...state,
				timestamp: new Date(state.timestamp.getTime() + minutes * 60 * 1000),
				liveMode: false,
			}));
		},

		// Step backward by minutes
		stepBackward: (minutes: number = 15) => {
			update(state => ({
				...state,
				timestamp: new Date(state.timestamp.getTime() - minutes * 60 * 1000),
				liveMode: false,
			}));
		},

		// Skip forward by hours
		skipForward: (hours: number = 1) => {
			update(state => ({
				...state,
				timestamp: new Date(state.timestamp.getTime() + hours * 60 * 60 * 1000),
				liveMode: false,
			}));
		},

		// Skip backward by hours
		skipBackward: (hours: number = 1) => {
			update(state => ({
				...state,
				timestamp: new Date(state.timestamp.getTime() - hours * 60 * 60 * 1000),
				liveMode: false,
			}));
		},

		// Set date range preset
		setDateRangePreset: (preset: DateRangePreset) => {
			const now = new Date();
			let start: Date, end: Date;
			switch (preset) {
				case '1h':
					start = new Date(now.getTime() - 60 * 60 * 1000);
					end = new Date(now.getTime() + 60 * 60 * 1000);
					break;
				case '7d':
					start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
					end = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
					break;
				default: // '24h'
					start = new Date(now.getTime() - 24 * 60 * 60 * 1000);
					end = new Date(now.getTime() + 24 * 60 * 60 * 1000);
			}
			update(state => ({ ...state, dateRange: { start, end } }));
		},

		// Set cache configuration
		setCacheConfig: (rangeHours: number, stepMinutes: number) => {
			update(state => ({ ...state, cacheRangeHours: rangeHours, cacheStepMinutes: stepMinutes }));
		},

		// Prefetch cache for timeline
		prefetchCache: async (baseUrl: string = 'http://localhost:8000') => {
			update(state => ({ ...state, cacheStatus: 'loading', cacheProgress: 0 }));

			try {
				let currentState: TreemapState = initialState;
				update(s => { currentState = s; return s; });

				// Generate timestamps for cache range
				const now = currentState.timestamp.getTime();
				const rangeMs = currentState.cacheRangeHours * 60 * 60 * 1000;
				const stepMs = currentState.cacheStepMinutes * 60 * 1000;
				const timestamps: string[] = [];

				for (let t = now - rangeMs; t <= now + rangeMs; t += stepMs) {
					timestamps.push(new Date(t).toISOString());
				}

				// Batch request
				const response = await fetch(`${baseUrl}/api/v1/treemap/batch`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						timestamps,
						occupancy_mode: currentState.occupancyMode,
						include_empty: currentState.includeEmpty,
					}),
				});

				if (!response.ok) throw new Error('Batch fetch failed');

				const result = await response.json();
				const newCache = new Map<string, TreemapResponse>();

				for (const [ts, data] of Object.entries(result.data)) {
					newCache.set(ts, data as TreemapResponse);
				}

				update(state => ({
					...state,
					timestampCache: newCache,
					cacheStatus: 'ready',
					cacheProgress: 100,
				}));
			} catch (err) {
				console.error('Cache prefetch failed:', err);
				update(state => ({ ...state, cacheStatus: 'error' }));
			}
		},

		// Get data for timestamp from cache
		getDataForTimestamp: (timestamp: Date): TreemapResponse | null => {
			let result: TreemapResponse | null = null;
			treemapStore.subscribe(state => {
				// Find closest cached timestamp
				const targetTime = timestamp.getTime();
				const stepMs = state.cacheStepMinutes * 60 * 1000;

				for (const [ts, data] of state.timestampCache.entries()) {
					const cachedTime = new Date(ts).getTime();
					if (Math.abs(cachedTime - targetTime) < stepMs / 2) {
						result = data;
						break;
					}
				}
			})();
			return result;
		},

		// Invalidate cache
		invalidateCache: () => {
			update(state => ({
				...state,
				timestampCache: new Map(),
				cacheStatus: 'idle',
				cacheProgress: 0,
			}));
		},

		// Set data directly (for cache hits)
		setData: (data: TreemapResponse) => {
			// Preserve zoom path so users can watch cells change color during playback
			update(state => ({ ...state, data }));
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
