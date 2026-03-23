import type { PageLoad } from './$types';
import { getRollCalls, getLocations, getLocationHierarchyPath, getRollCall } from '$lib/services/api';

export const load: PageLoad = async () => {
  try {
    const [rollcalls, locations] = await Promise.all([getRollCalls(), getLocations()]);

    // For each rollcall summary try to fetch the full rollcall details (which include route stops)
    const detailsPromises = (rollcalls || []).map((rc: any) =>
      // fetch detailed rollcall; don't let one failure break everything
      getRollCall(rc.id).then((d) => ({ ok: true, id: rc.id, detail: d })).catch((e) => ({ ok: false, id: rc.id, error: e }))
    );

    const detailsResults = await Promise.all(detailsPromises);

    const normalized = (rollcalls || []).map((rc: any) => {
      let location_name: string | null = rc.location_name ?? null;

      // If we fetched details, try to extract from the first route stop
      const dr = detailsResults.find((r: any) => r.id === rc.id && r.ok && r.detail);
      const detail = dr ? dr.detail : null;

      if (!location_name && detail && Array.isArray(detail.route) && detail.route.length > 0) {
        const stop = detail.route[0];
        if (stop.location_name) location_name = stop.location_name;
        else if (stop.location_id) {
          const loc = locations.find((l: any) => l.id === stop.location_id);
          if (loc) {
            try {
              location_name = getLocationHierarchyPath(loc, locations);
            } catch {
              location_name = loc.name ?? stop.location_id;
            }
          } else {
            location_name = stop.location_id;
          }
        }
      }

      // Final fallback: if rollcall summary had a location_id or mapping via locations
      if (!location_name && rc.location_id) {
        const loc = locations.find((l: any) => l.id === rc.location_id);
        if (loc) location_name = getLocationHierarchyPath(loc, locations);
        else location_name = rc.location_id;
      }

      if (!location_name) location_name = 'Unknown location';

      return {
        ...rc,
        location_name
      };
    });

    return { rollcalls: normalized, locations };
  } catch (err) {
    // Loader should not throw for the POC; return empty list and error flag
    return { rollcalls: [], error: (err as Error)?.message ?? 'Failed to load roll calls' };
  }
};

