import type { PageLoad } from './$types';
import { getRollCall } from '$lib/services/api';

export const load: PageLoad = async ({ params }) => {
  const id = params.id;
  try {
    const rollCall = await getRollCall(id);
    return { rollCall };
  } catch (err) {
    console.error('Failed to load roll call for execute', err);
    return { rollCall: null, error: 'Failed to load roll call' };
  }
};

