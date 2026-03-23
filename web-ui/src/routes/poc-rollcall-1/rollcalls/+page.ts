import type { PageLoad } from './$types';
import { getRollCalls } from '$lib/services/api';

export const load: PageLoad = async () => {
  try {
    const rollcalls = await getRollCalls();
    return { rollcalls };
  } catch (err) {
    // Loader should not throw for the POC; return empty list and error flag
    return { rollcalls: [], error: (err as Error)?.message ?? 'Failed to load roll calls' };
  }
};

