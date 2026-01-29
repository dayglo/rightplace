import type { PageLoad } from './$types';
import { getInmate } from '$lib/services/api';

export const load: PageLoad = async ({ params }) => {
	const inmate = await getInmate(params.id);
	return {
		inmate
	};
};
