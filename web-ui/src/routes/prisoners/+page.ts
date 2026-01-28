import type { PageLoad } from './$types';
import { getInmates } from '$lib/services/api';

export const load: PageLoad = async () => {
	const inmates = await getInmates();
	return {
		inmates
	};
};
