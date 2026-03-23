<script lang="ts">
  import StatusBadge from '$lib/components/poc-rollcall-1/StatusBadge.svelte';
  export let rollcall: any;
  export let selected: boolean = false;
</script>

<article role="listitem" class="bg-white rounded-lg shadow-sm p-4 mb-3" class:selected={selected}>
  <div class="flex items-start justify-between">
    <div class="flex-1 min-w-0">
      <h3 class="text-sm font-semibold text-gray-900 truncate">{rollcall.name}</h3>
      <p class="text-xs text-gray-500 mt-1">Scheduled: {new Date(rollcall.scheduled_at ?? rollcall.scheduled_time ?? rollcall.scheduled).toLocaleString()}</p>
    </div>
        <div class="ml-3 flex-shrink-0 text-right">
          <StatusBadge status={rollcall.status} />
        </div>
  </div>

  <div class="mt-3 text-xs text-gray-600 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <span class="font-medium">{rollcall.expected_inmates ?? rollcall.expected_prisoners ?? rollcall.expected}</span>
      <span class="text-gray-400">inmates</span>
    </div>
    <div class="text-right">
      <div class="text-xs text-gray-500">Stops: {rollcall.total_stops ?? rollcall.total_locations ?? rollcall.totalStops ?? 0}</div>
      <div class="text-xs text-gray-500">Progress: {Math.round((rollcall.progress_percentage ?? 0))}%</div>
    </div>
  </div>
</article>

<style>
  :global(.selected) {
    border: 2px solid #2563eb; /* blue-600 */
  }
</style>

