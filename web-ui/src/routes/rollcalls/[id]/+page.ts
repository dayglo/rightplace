import type { PageLoad } from './$types';
import { getRollCall, getRollCallVerifications, getLocations, getInmates } from '$lib/services/api';
import { error } from '@sveltejs/kit';

export const load: PageLoad = async ({ params }) => {
	try {
		const [rollCall, verifications, locations, inmates] = await Promise.all([
			getRollCall(params.id),
			getRollCallVerifications(params.id),
			getLocations(),
			getInmates()
		]);

		return {
			rollCall,
			verifications,
			locations,
			inmates
		};
	} catch (err) {
		console.error('Failed to load roll call:', err);
		throw error(404, 'Roll call not found');
	}
};
