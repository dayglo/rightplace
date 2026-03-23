<script lang="ts">
  export let status: string | undefined;
  export let rollcall: any = null;
  import { goto } from '$app/navigation';

  function bgFor(s: string | undefined) {
	switch (s) {
	  case 'in_progress':
		return 'bg-yellow-100 text-yellow-800';
	  case 'completed':
		return 'bg-green-100 text-green-800';
	  case 'cancelled':
		return 'bg-red-100 text-red-800';
	  default:
		return 'bg-gray-100 text-gray-800';
	}
  }

  function continueExec() {
	if (rollcall && rollcall.id) {
	  goto(`/poc-rollcall-1/rollcalls/${rollcall.id}/execute`);
	}
  }
</script>

{#if status}
  <div style="display:flex; flex-direction:column; align-items:flex-end; gap:6px">
	<div class={bgFor(status)} style="padding:4px 8px;border-radius:999px;font-size:12px;font-weight:600">{status.replace('_',' ')}</div>
	{#if status === 'in_progress'}
	  <button on:click={continueExec} style="padding:4px 8px;border-radius:6px;border:none;background:#0ea5a3;color:white;font-size:12px">Continue</button>
	{/if}
  </div>
{:else}
  <div></div>
{/if}


