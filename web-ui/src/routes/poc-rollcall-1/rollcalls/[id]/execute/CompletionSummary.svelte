<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  export let verified: any[] = [];
  const dispatch = createEventDispatcher();

  function complete() {
    dispatch('complete');
  }

  function cancel() {
    dispatch('cancel');
  }
</script>

<style>
  .panel { background:#fff; padding:1rem; border-radius:8px; box-shadow:0 1px 2px rgba(0,0,0,0.06) }
</style>

<div class="panel">
  <h3>Roll call complete</h3>
  <div style="margin-top:0.5rem">Actions recorded: {verified.length}</div>
  <div style="margin-top:0.5rem; display:flex; gap:8px; justify-content:flex-end">
    <button on:click={cancel}>Cancel</button>
    <button on:click={complete}>Complete roll call</button>
  </div>
</div>

