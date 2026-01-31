import type { PageLoad } from './$types';
import { getLocation } from '$lib/services/api';

export const load: PageLoad = async ({ params }) => {
	const location = await getLocation(params.id);
	return {
		location
	};
};
