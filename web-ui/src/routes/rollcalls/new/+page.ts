import type { PageLoad } from './$types';
import { getLocations, getInmates } from '$lib/services/api';

export const load: PageLoad = async () => {
	const [locations, inmates] = await Promise.all([
		getLocations(),
		getInmates()
	]);

	return {
		locations,
		inmates
	};
};
