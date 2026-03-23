import type { PageLoad } from './$types';
import { getRollCall, getLocations, getLocationHierarchyPath } from '$lib/services/api';

export const load: PageLoad = async ({ params }) => {
  const id = params.id;
  try {
    const rollCall = await getRollCall(id);

    // Fetch locations to build human-readable location names for stops
    try {
      const locations = await getLocations();
      if (rollCall?.route && Array.isArray(rollCall.route)) {
        for (const stop of rollCall.route) {
          if (!stop.location_name && stop.location_id) {
            const loc = locations.find((l: any) => l.id === stop.location_id);
            if (loc) {
              try {
                stop.location_name = getLocationHierarchyPath(loc, locations);
              } catch {
                stop.location_name = loc.name ?? stop.location_id;
              }
            } else {
              stop.location_name = stop.location_id;
            }
          }
        }
      }

      return { rollCall, locations };
    } catch (innerErr) {
      console.warn('Could not fetch locations for preview, showing ids', innerErr);
      return { rollCall };
    }
  } catch (err) {
    console.error('Failed to load roll call', err);
    return { rollCall: null, error: 'Failed to load roll call' };
  }
};

