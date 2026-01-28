import { getInmates, getLocations, getRollCalls } from '$lib/services/api';

export const load = async () => {
	try {
		const [inmates, locations, rollCalls] = await Promise.all([
			getInmates(),
			getLocations(),
			getRollCalls()
		]);

		return {
			inmates,
			locations,
			rollCalls
		};
	} catch (error) {
		console.error('Failed to load dashboard data:', error);
		return {
			inmates: [],
			locations: [],
			rollCalls: []
		};
	}
};
