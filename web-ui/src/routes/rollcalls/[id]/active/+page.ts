import type { PageLoad } from './$types';
import { getRollCall, getLocations, getInmates, getRollCallVerifications } from '$lib/services/api';
import { error } from '@sveltejs/kit';

export const load: PageLoad = async ({ params }) => {
	try {
		const [rollCall, locations, inmates, existingVerifications] = await Promise.all([
			getRollCall(params.id),
			getLocations(),
			getInmates(),
			getRollCallVerifications(params.id)
		]);

		// Check that roll call is in progress
		if (rollCall.status !== 'in_progress') {
			throw error(400, 'Roll call is not in progress');
		}

		return {
			rollCall,
			locations,
			inmates,
			existingVerifications
		};
	} catch (err) {
		console.error('Failed to load active roll call:', err);
		if (err && typeof err === 'object' && 'status' in err) {
			throw err;
		}
		throw error(404, 'Roll call not found');
	}
};
