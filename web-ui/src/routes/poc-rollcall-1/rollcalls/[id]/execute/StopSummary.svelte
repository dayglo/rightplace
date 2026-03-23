<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  export let verified: any[] = [];
  const dispatch = createEventDispatcher();

  function proceed() {
    dispatch('proceed');
  }

  function rescan() {
    dispatch('rescan');
  }
</script>

<style>
  .panel { background:#fff; padding:1rem; border-radius:8px; box-shadow:0 1px 2px rgba(0,0,0,0.06) }
</style>

<div class="panel">
  <h3>Stop summary</h3>
  <div style="margin-top:0.5rem">Total actions: {verified.length}</div>
  <div style="margin-top:0.5rem; display:flex; gap:8px; justify-content:flex-end">
    <button on:click={rescan}>Re-scan missed</button>
    <button on:click={proceed}>Proceed to next stop</button>
  </div>
</div>

