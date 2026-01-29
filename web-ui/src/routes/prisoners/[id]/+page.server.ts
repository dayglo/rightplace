import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import {
	getInmate,
	getInmateSchedule,
	getInmateVerifications,
	getLocations
} from '$lib/services/api';

export const load: PageServerLoad = async ({ params }) => {
	try {
		const [inmate, schedules, verifications, locations] = await Promise.all([
			getInmate(params.id),
			getInmateSchedule(params.id),
			getInmateVerifications(params.id, 10),
			getLocations()
		]);

		return {
			inmate,
			schedules,
			verifications,
			locations
		};
	} catch (err) {
		console.error('Error loading prisoner detail:', err);
		throw error(404, 'Prisoner not found');
	}
};
