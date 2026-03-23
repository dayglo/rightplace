<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { startRollCall, getExpectedPrisoners, getRollCall } from '$lib/services/api';

  export let data: any;

  let rollCall = data?.rollCall ?? null;
  let isStarting = false;

  type PerStop = {
    loading: boolean;
    error?: string | null;
    inmates?: any[];
    expanded: boolean;
  };

  // Map location_id -> PerStop
  let perStop: Record<string, PerStop> = {};

  function ensureStopEntry(locationId: string) {
    if (!perStop[locationId]) {
      perStop[locationId] = { loading: false, error: null, inmates: undefined, expanded: false };
    }
  }

  async function toggleStop(stop: any) {
    const loc = stop.location_id;
    ensureStopEntry(loc);
    perStop[loc].expanded = !perStop[loc].expanded;
    if (perStop[loc].expanded && !perStop[loc].inmates) {
      perStop[loc].loading = true;
      try {
        const res = await getExpectedPrisoners(loc);
        // add image state flags for each inmate so we can hide initials after image loads
        const items = (res.expected_prisoners ?? []).map((i: any) => ({ ...i, _imageLoaded: false, _imageError: false }));
        perStop[loc].inmates = items;
      } catch (err) {
        console.error('Failed to load expected prisoners for', loc, err);
        perStop[loc].error = 'Failed to load prisoners';
      } finally {
        perStop[loc].loading = false;
      }
    }
  }

  function imageLoaded(locationId: string, inmate: any) {
    inmate._imageLoaded = true;
    // force Svelte to notice the change by shallow-copying the array
    perStop[locationId].inmates = perStop[locationId].inmates.slice();
  }

  function imageError(locationId: string, inmate: any) {
    inmate._imageError = true;
    perStop[locationId].inmates = perStop[locationId].inmates.slice();
  }

  function formatTimeEstimate(seconds: number | undefined) {
    if (!seconds) return '-';
    const mins = Math.round(seconds / 60);
    return `${mins} min`;
  }

  async function onStart() {
    if (!rollCall) return;
    // If roll call is already in progress, just continue
    if (rollCall.status === 'in_progress') {
      goto(`/poc-rollcall-1/rollcalls/${rollCall.id}/execute`);
      return;
    }

    const ok = confirm('Start roll call now?');
    if (!ok) return;
    isStarting = true;
    try {
      await startRollCall(rollCall.id);
      // navigate to execute page
      goto(`/poc-rollcall-1/rollcalls/${rollCall.id}/execute`);
    } catch (err) {
      console.error('Failed to start roll call', err);
      // Re-fetch roll call in case another client started it meanwhile
      try {
        const fresh = await getRollCall(rollCall.id);
        if (fresh?.status === 'in_progress') {
          // update local rollCall and continue
          rollCall = fresh;
          goto(`/poc-rollcall-1/rollcalls/${rollCall.id}/execute`);
          return;
        }
      } catch (innerErr) {
        console.warn('Failed to refresh roll call after start failure', innerErr);
      }
      alert('Failed to start roll call');
    } finally {
      isStarting = false;
    }
  }

  // Basic defensive handling in case loader returned error
  onMount(() => {
    if (!rollCall) {
      console.warn('Preview: no rollCall data');
    }
  });
</script>

<style>
  .page { padding: 1rem; }
  .header { display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.5rem; }
  .banner { background:#fffbeb; border:1px solid #fef3c7; color:#92400e; padding:0.5rem 0.75rem; border-radius:6px; margin-bottom:0.75rem }
  .card { background: #fff; border-radius: 8px; padding: 0.75rem; box-shadow: 0 1px 2px rgba(0,0,0,0.04); margin-bottom: 0.75rem; }
  .stop { padding: 0.5rem 0; border-bottom: 1px solid #eee; }
  .stop:last-child { border-bottom: none; }
  .start-btn { position: fixed; left: 1rem; right: 1rem; bottom: 1rem; }
  button.primary { background: #0ea5a3; color: white; border: none; padding: 0.75rem 1rem; border-radius: 8px; width: 100%; font-weight: 600; }
  .inmate-row { display:flex; gap:12px; align-items:center }
  .avatar { width:40px; height:40px; border-radius:999px; background:#e5e7eb; display:inline-flex; align-items:center; justify-content:center; font-weight:600; color:#374151; overflow:hidden; flex-shrink:0 }
  .avatar img { width:100%; height:100%; object-fit:cover; display:block }
  .initials { font-size:0.95rem; line-height:1; }
</style>

<div class="page">
  <div class="header">
    <h2>{rollCall ? rollCall.name ?? `Roll Call ${rollCall.id}` : 'Roll Call Preview'}</h2>
    {#if rollCall}
      <small>{new Date(rollCall.scheduled_time ?? rollCall.scheduled_at ?? rollCall.scheduled).toLocaleString()}</small>
    {/if}
  </div>

  {#if !rollCall}
    <div class="card">No roll call data available.</div>
  {:else}
    {#if rollCall.status === 'in_progress'}
      <div class="banner">
        This roll call is already in progress. You can continue execution where it was left off.
        <button style="margin-left:12px;padding:0.25rem 0.5rem;border-radius:6px;border:none;background:#0ea5a3;color:white;font-weight:600" on:click={() => goto(`/poc-rollcall-1/rollcalls/${rollCall.id}/execute`)}>Continue</button>
      </div>
    {/if}
    <div class="card">
      <div><strong>Stops:</strong> {rollCall.route?.length ?? 0}</div>
      <div><strong>Estimated time:</strong> {formatTimeEstimate(rollCall.estimated_time_seconds)}</div>
      <div style="margin-top:0.5rem"><em>Tap a stop to expand (not implemented)</em></div>
    </div>

        <div class="card">
          <h3>Route stops</h3>
          {#if rollCall.route && rollCall.route.length > 0}
            <div>
              {#each rollCall.route as stop (stop.location_id)}
                {#key stop.location_id}
                  <div class="stop">
                    <div style="display:flex; justify-content:space-between; align-items:center">
                      <div style="flex:1">
                        <div style="font-weight:600">{stop.location_name ?? stop.location_id}</div>
                        <div style="font-size:0.9rem; color:#666">Expected: {stop.expected_inmates ? stop.expected_inmates.length : '-'}</div>
                      </div>
                      <div style="margin-left:8px">
                        <button on:click={() => toggleStop(stop)} aria-expanded={perStop[stop.location_id]?.expanded ? 'true' : 'false'} style="background:transparent;border:none;font-size:1.2rem">{perStop[stop.location_id]?.expanded ? '▾' : '▸'}</button>
                      </div>
                    </div>

                    {#if perStop[stop.location_id]?.expanded}
                      <div style="margin-top:0.5rem">
                        {#if perStop[stop.location_id].loading}
                          <div>Loading inmates…</div>
                        {:else if perStop[stop.location_id].error}
                          <div style="color:crimson">{perStop[stop.location_id].error}</div>
                        {:else}
                          {#if perStop[stop.location_id].inmates && perStop[stop.location_id].inmates.length > 0}
                            <ul style="padding-left:0; list-style:none; margin:0">
                              {#each perStop[stop.location_id].inmates as inmate}
                                <li style="padding:0.5rem 0; border-bottom:1px solid #f0f0f0">
                                  <div class="inmate-row">
                                    <div class="avatar" aria-hidden="true">
                                      {#if (inmate.photo_uri || inmate.avatar_url || inmate.image_url)}
                                        <img src={inmate.photo_uri ?? inmate.avatar_url ?? inmate.image_url}
                                          alt="{inmate.first_name} {inmate.last_name}"
                                          loading="lazy"
                                          on:load={() => imageLoaded(stop.location_id, inmate)}
                                          on:error={() => imageError(stop.location_id, inmate)}
                                        />
                                      {/if}
                                      {#if !(inmate._imageLoaded && !inmate._imageError)}
                                        <span class="initials">{(inmate.first_name ? inmate.first_name.charAt(0) : '')}{(inmate.last_name ? inmate.last_name.charAt(0) : '')}</span>
                                      {/if}
                                    </div>

                                    <div style="flex:1">
                                      <div style="font-weight:600">{inmate.first_name} {inmate.last_name}</div>
                                      <div style="font-size:0.9rem; color:#666">#{inmate.inmate_number}</div>
                                    </div>

                                    <div style="flex-shrink:0">
                                      {#if inmate.is_enrolled}
                                        <span style="background:#10b981;color:white;padding:0.25rem 0.5rem;border-radius:999px;font-size:0.85rem">Enrolled</span>
                                      {:else}
                                        <span style="background:#f59e0b;color:white;padding:0.25rem 0.5rem;border-radius:999px;font-size:0.85rem">Not enrolled</span>
                                      {/if}
                                    </div>
                                  </div>
                                </li>
                              {/each}
                            </ul>
                          {:else}
                            <div style="color:#666">No inmates expected at this location.</div>
                          {/if}
                        {/if}
                      </div>
                    {/if}
                  </div>
                {/key}
              {/each}
            </div>
          {:else}
            <div>No stops defined for this roll call.</div>
          {/if}
        </div>

    <div style="height:64px"></div>

    <div class="start-btn">
      <button class="primary" on:click={onStart} disabled={isStarting}>{isStarting ? 'Starting…' : (rollCall?.status === 'in_progress' ? 'Continue Roll Call' : 'Start Roll Call')}</button>
    </div>
  {/if}
</div>

