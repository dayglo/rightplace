<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  let selectedInmateId = '';
  let status: 'verified' | 'not_found' | 'manual' = 'verified';
  let notes = '';
  let reason = '';

  function submit() {
    dispatch('submit', { inmate_id: selectedInmateId, status, notes, reason, confidence: 0 });
  }

  function cancel() {
    dispatch('cancel');
  }
</script>

<style>
  .modal { position:fixed; left:0; right:0; top:0; bottom:0; background:rgba(0,0,0,0.4); display:flex; align-items:center; justify-content:center }
  .panel { background:#fff; padding:1rem; border-radius:8px; width:90%; max-width:420px }
</style>

<div class="modal" role="dialog" aria-modal="true">
  <div class="panel">
    <h3>Manual verification</h3>
    <div style="margin-top:0.5rem">
      <label>Inmate ID (optional)</label>
      <input bind:value={selectedInmateId} placeholder="enter inmate id" style="width:100%; padding:0.5rem; margin-top:0.25rem" />
    </div>

    <div style="margin-top:0.5rem">
      <label>Action</label>
      <select bind:value={status} style="width:100%; padding:0.5rem; margin-top:0.25rem">
        <option value="verified">Mark Verified</option>
        <option value="not_found">Mark Not Found</option>
        <option value="manual">Other / Manual</option>
      </select>
    </div>

    <div style="margin-top:0.5rem">
      <label>Reason / Notes</label>
      <textarea bind:value={notes} rows={3} style="width:100%; padding:0.5rem; margin-top:0.25rem"></textarea>
    </div>

    <div style="display:flex; gap:8px; justify-content:flex-end; margin-top:0.75rem">
      <button on:click={cancel}>Cancel</button>
      <button on:click={submit}>Submit</button>
    </div>
  </div>
</div>

