import type { PageLoad } from './$types';
import { getLocations } from '$lib/services/api';

export const load: PageLoad = async () => {
	const locations = await getLocations();
	return {
		locations
	};
};
