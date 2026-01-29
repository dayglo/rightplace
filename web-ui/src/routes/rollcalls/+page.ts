import type { PageLoad } from './$types';
import { getRollCalls } from '$lib/services/api';

export const load: PageLoad = async () => {
	const rollcalls = await getRollCalls();
	return {
		rollcalls
	};
};
