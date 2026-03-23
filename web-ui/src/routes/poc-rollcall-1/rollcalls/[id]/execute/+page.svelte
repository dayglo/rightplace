<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { recordVerification, completeRollCall, getRollCallVerifications } from '$lib/services/api';
  import InmateCard from './InmateCard.svelte';
  import ManualOverride from './ManualOverride.svelte';
  import StopSummary from './StopSummary.svelte';
  import CompletionSummary from './CompletionSummary.svelte';

  export let data: any;

  let rollCall = data?.rollCall ?? null;
  let error = data?.error ?? null;

  // Execution state
  let currentStopIndex = 0;
  let currentInmateIndex = 0;
  let verified: any[] = []; // local records
  let showManual = false;
  let showStopSummary = false;
  let showCompletion = false;

  // Provide a persistent simple queue for offline/manual testing
  const QUEUE_KEY = `poc_exec_queue_${rollCall?.id ?? 'unknown'}`;

  function getQueue() {
    try {
      const raw = localStorage.getItem(QUEUE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      console.warn('Failed to read queue', e);
      return [];
    }
  }

  function pushQueue(item: any) {
    const q = getQueue();
    q.push(item);
    localStorage.setItem(QUEUE_KEY, JSON.stringify(q));
  }

  function clearQueue() {
    localStorage.removeItem(QUEUE_KEY);
  }

  function currentStop() {
    return rollCall?.route?.[currentStopIndex];
  }

  function currentInmate() {
    const stop = currentStop();
    return stop?.expected_inmates?.[currentInmateIndex];
  }

  function advance() {
    const stop = currentStop();
    if (!stop) return;
    if (currentInmateIndex + 1 < (stop.expected_inmates?.length ?? 0)) {
      currentInmateIndex += 1;
    } else {
      // end of stop
      showStopSummary = true;
    }
  }

  async function onManualRecord(payload: any) {
    // Save locally and attempt to send to API; if fails, queue it
    const record = {
      inmate_id: payload.inmate_id,
      location_id: currentStop()?.location_id,
      status: payload.status,
      confidence: payload.confidence ?? 0,
      is_manual_override: true,
      manual_override_reason: payload.reason ?? null,
      notes: payload.notes ?? null,
      timestamp: new Date().toISOString()
    };

    verified.push(record);

    try {
      await recordVerification(rollCall.id, record);
    } catch (err) {
      console.warn('recordVerification failed, queuing', err);
      pushQueue({ op: 'recordVerification', payload: record });
    }

    // advance to next inmate
    advance();
  }

  async function onProceedToNextStop() {
    // mark stop complete locally and advance indices
    currentStopIndex += 1;
    currentInmateIndex = 0;
    showStopSummary = false;

    if (currentStopIndex >= (rollCall?.route?.length ?? 0)) {
      // finished all stops
      showCompletion = true;
    }
  }

  async function onCompleteRollCall() {
    try {
      await completeRollCall(rollCall.id);
      clearQueue();
      goto(`/poc-rollcall-1/rollcalls`);
    } catch (err) {
      alert('Failed to complete roll call (offline?). Your results are queued.');
      pushQueue({ op: 'completeRollCall', payload: { rollCallId: rollCall.id } });
    }
  }

  onMount(() => {
    // simple attempt to flush queue if any (non-blocking)
    const q = getQueue();
    if (q.length > 0 && navigator.onLine) {
      (async () => {
        for (const item of q) {
          try {
            if (item.op === 'recordVerification') {
              await recordVerification(rollCall.id, item.payload);
            } else if (item.op === 'completeRollCall') {
              await completeRollCall(rollCall.id);
            }
          } catch (e) {
            console.warn('Failed to flush queued item', item, e);
          }
        }
        clearQueue();
      })();
    }
  });
</script>

<style>
  .page { padding: 1rem; }
  .footer-space { height: 84px; }
  .header { display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.5rem; }
</style>

<div class="page">
  <div class="header">
    <div>
      <h2>{rollCall ? rollCall.name ?? `Roll Call ${rollCall.id}` : 'Execute Roll Call'}</h2>
      {#if rollCall}
        <small>{new Date(rollCall.scheduled_time ?? rollCall.scheduled_at ?? rollCall.scheduled).toLocaleString()}</small>
      {/if}
    </div>
    <div>
      <button on:click={() => goto(`/poc-rollcall-1/rollcalls/${rollCall?.id}/preview`)}>Preview</button>
    </div>
  </div>

  {#if !rollCall}
    <div>No roll call loaded.</div>
  {:else}
    {#if currentStop()}
      <div style="margin-bottom:0.75rem">
        <div style="font-weight:600">Stop: {currentStop().location_name ?? currentStop().location_id}</div>
        <div style="color:#666">{currentInmateIndex + 1} of {currentStop().expected_inmates?.length ?? 0}</div>
      </div>

      {#if currentInmate()}
        <InmateCard {currentInmate} />

        <div style="display:flex; gap:8px; margin-top:0.75rem">
          <button on:click={() => { showManual = true; }}>Manual Verify</button>
          <button on:click={() => { verified.push({ inmate_id: currentInmate().inmate_id, status: 'not_found', timestamp: new Date().toISOString() }); advance(); }}>Mark Not Found</button>
          <button on:click={() => { verified.push({ inmate_id: currentInmate().inmate_id, status: 'skipped', timestamp: new Date().toISOString() }); advance(); }}>Skip</button>
        </div>
      {:else}
        <div>No inmates expected at this stop.</div>
      {/if}
    {:else}
      <div>No stops defined for this roll call.</div>
    {/if}

    {#if showManual}
      <ManualOverride on:submit={(e) => { showManual = false; onManualRecord(e.detail); }} on:cancel={() => (showManual = false)} />
    {/if}

    {#if showStopSummary}
      <StopSummary {verified} on:proceed={() => onProceedToNextStop()} on:rescan={() => { showStopSummary = false; currentInmateIndex = 0; }} />
    {/if}

    {#if showCompletion}
      <CompletionSummary {verified} on:complete={() => onCompleteRollCall()} on:cancel={() => goto(`/poc-rollcall-1/rollcalls`)} />
    {/if}

    <div class="footer-space"></div>
  {/if}
</div>

