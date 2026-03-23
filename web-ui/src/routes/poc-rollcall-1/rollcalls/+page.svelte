<script lang="ts">
  import { onMount } from 'svelte';
  import RollCallCard from '$lib/components/poc-rollcall-1/RollCallCard.svelte';

  export let data: any;

  let rollcalls = data?.rollcalls ?? [];
  let error: string | null = data?.error ?? null;

  // officer selection and location
  let officers: string[] = [];
  let selectedOfficer: string = '';
  let officerLocation: string | null = null;

  let filtered = [] as any[];
  // default to scheduled per requirement
  let filter = 'scheduled';
  let loading = false;
  let offline = !navigator.onLine;
  const STORAGE_KEY = 'poc-rollcall-1.rollcalls.v1';

  // selected rollcall id (nearest)
  let selectedRollcallId: string | null = null;

  function applyFilter() {
    // If no officer selected, show nothing (user must pick an officer first)
    if (!selectedOfficer) {
      filtered = [];
      selectedRollcallId = null;
      return;
    }

    // base set for the selected officer
    let base = rollcalls.filter((r: any) => r.officer_id === selectedOfficer);

    if (filter === 'all') {
      filtered = base;
    } else {
      filtered = base.filter((r: any) => r.status === filter);
    }

    // sort by scheduled time ascending
    filtered.sort((a: any, b: any) => {
      const ta = new Date(a.scheduled_at ?? a.scheduled_time ?? a.scheduled).getTime() || 0;
      const tb = new Date(b.scheduled_at ?? b.scheduled_time ?? b.scheduled).getTime() || 0;
      return ta - tb;
    });

    computeNearestSelection();
  }

  function computeNearestSelection() {
    selectedRollcallId = null;
    if (!filtered || filtered.length === 0) return;
    const now = Date.now();
    // prefer upcoming rollcalls (scheduled >= now)
    const upcoming = filtered.filter((r: any) => (new Date(r.scheduled_at ?? r.scheduled_time ?? r.scheduled).getTime() || 0) >= now);
    const candidates = upcoming.length ? upcoming : filtered;
    let best: any = null;
    let bestDiff = Number.POSITIVE_INFINITY;
    for (const r of candidates) {
      const t = new Date(r.scheduled_at ?? r.scheduled_time ?? r.scheduled).getTime() || 0;
      const diff = Math.abs(t - now);
      if (diff < bestDiff) {
        bestDiff = diff;
        best = r;
      }
    }
    if (best) selectedRollcallId = best.id;
  }

  function setOfficerLocationManual(val: string) {
    officerLocation = val;
    const key = 'poc-rollcall-1.officer-locations';
    let map: Record<string, string> = {};
    try {
      map = JSON.parse(localStorage.getItem(key) || '{}');
    } catch {
      map = {};
    }
    if (selectedOfficer) {
      map[selectedOfficer] = val;
      localStorage.setItem(key, JSON.stringify(map));
    }
  }

  async function refresh() {
    loading = true;
    error = null;
    try {
      const mod = await import('$lib/services/api');
      const fresh = await mod.getRollCalls();
      rollcalls = fresh;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(fresh));
      // rebuild officers list when new data arrives
      const ids = new Set<string>();
      for (const r of rollcalls) if (r.officer_id) ids.add(r.officer_id);
      officers = Array.from(ids);
      applyFilter();
    } catch (err) {
      error = (err as Error)?.message ?? 'Failed to refresh';
      const cached = localStorage.getItem(STORAGE_KEY);
      if (cached) {
        try {
          rollcalls = JSON.parse(cached);
          applyFilter();
        } catch {
          // ignore
        }
      }
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    // initialize officers from loader data
    const ids = new Set<string>();
    for (const r of rollcalls) if (r.officer_id) ids.add(r.officer_id);
    officers = Array.from(ids);

    // try to preselect if only one officer exists
    if (officers.length === 1) {
      selectedOfficer = officers[0];
      // load cached officer location if present
      try {
        const mapRaw = localStorage.getItem('poc-rollcall-1.officer-locations');
        if (mapRaw) {
          const map = JSON.parse(mapRaw);
          officerLocation = map[selectedOfficer] ?? null;
        }
      } catch {}
    }

    if ((!rollcalls || rollcalls.length === 0) && localStorage.getItem(STORAGE_KEY)) {
      try {
        rollcalls = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
      } catch {
        rollcalls = [];
      }
    }

    applyFilter();

    const onOnline = () => (offline = false);
    const onOffline = () => (offline = true);
    window.addEventListener('online', onOnline);
    window.addEventListener('offline', onOffline);
    return () => {
      window.removeEventListener('online', onOnline);
      window.removeEventListener('offline', onOffline);
    };
  });
</script>

<header class="px-4 py-3 bg-white border-b sticky top-0 z-10">
  <div class="flex items-center justify-between">
    <h1 class="text-lg font-semibold">Roll Calls</h1>
    <div class="flex items-center gap-2">
      {#if offline}
        <span class="text-xs text-red-600">Offline</span>
      {/if}
      <button class="px-3 py-2 bg-gray-100 rounded-md text-sm" on:click={refresh} aria-label="Refresh roll calls">
        {#if loading}Refreshing...{:else}Refresh{/if}
      </button>
    </div>
  </div>

  <div class="mt-3 space-y-3">
    <div>
      <label class="block text-xs font-medium text-gray-700">Officer</label>
      <select bind:value={selectedOfficer} on:change={() => { applyFilter(); }} class="w-full rounded-md border p-2 text-sm">
        <option value="">-- Select officer --</option>
        {#each officers as o}
          <option value={o}>{o}</option>
        {/each}
      </select>
    </div>

    <div>
      <label class="block text-xs font-medium text-gray-700">Officer location</label>
      <div class="flex gap-2 items-center">
        <input class="flex-1 rounded-md border p-2 text-sm" placeholder="Unknown" bind:value={officerLocation} />
        <button class="px-3 py-2 bg-gray-100 rounded-md text-sm" on:click={() => setOfficerLocationManual(officerLocation ?? '')}>Save</button>
      </div>
      {#if officerLocation}
        <div class="text-xs text-gray-500 mt-1">Location: {officerLocation}</div>
      {:else}
        <div class="text-xs text-gray-400 mt-1">Location not available</div>
      {/if}
    </div>

    <div>
      <label class="block text-xs font-medium text-gray-700">Filter</label>
      <select bind:value={filter} on:change={applyFilter} class="w-full rounded-md border p-2 text-sm">
        <option value="all">All</option>
        <option value="scheduled">Scheduled</option>
        <option value="in_progress">In progress</option>
        <option value="completed">Completed</option>
      </select>
    </div>
  </div>
</header>

<main class="p-4 bg-slate-50 min-h-screen">
  {#if error}
    <div class="bg-red-50 text-red-700 p-3 rounded mb-3">{error}</div>
  {/if}

  {#if loading && (!filtered || filtered.length === 0)}
    <div class="animate-pulse space-y-3">
      <div class="h-16 bg-white rounded-lg"></div>
      <div class="h-16 bg-white rounded-lg"></div>
      <div class="h-16 bg-white rounded-lg"></div>
    </div>
  {:else}
    {#if filtered && filtered.length > 0}
      <section role="list">
        {#each filtered as r (r.id)}
          <RollCallCard rollcall={r} selected={r.id === selectedRollcallId} />
        {/each}
      </section>
    {:else}
      <div class="text-center text-sm text-gray-600 mt-8">
        <p>No roll calls found.</p>
        <button class="mt-3 px-4 py-2 bg-blue-600 text-white rounded" on:click={refresh}>Try refresh</button>
      </div>
    {/if}
  {/if}
</main>

