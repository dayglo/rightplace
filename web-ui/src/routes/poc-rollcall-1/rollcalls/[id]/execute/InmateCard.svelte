<script lang="ts">
  export let currentInmate: any;
</script>

<style>
  .card { background:#fff; padding:0.75rem; border-radius:8px; box-shadow:0 1px 2px rgba(0,0,0,0.04)}
  .avatar { width:72px; height:72px; border-radius:999px; background:#e5e7eb; display:inline-flex; align-items:center; justify-content:center; font-weight:600; color:#374151; overflow:hidden }
</style>

<div class="card">
  <div style="display:flex; gap:12px; align-items:center">
    <div class="avatar" aria-hidden="true">
      {#if currentInmate.photo_uri}
        <img src={currentInmate.photo_uri} alt="{currentInmate.first_name} {currentInmate.last_name}" style="width:100%;height:100%;object-fit:cover" />
      {:else}
        <div style="font-size:1.25rem">{(currentInmate.first_name?.charAt(0) ?? '')}{(currentInmate.last_name?.charAt(0) ?? '')}</div>
      {/if}
    </div>

    <div style="flex:1">
      <div style="font-weight:600">{currentInmate.first_name} {currentInmate.last_name}</div>
      <div style="color:#666">#{currentInmate.inmate_number}</div>
      {#if currentInmate.is_enrolled === false}
        <div style="margin-top:0.5rem"><strong style="color:#b45309">Not enrolled</strong></div>
      {/if}
    </div>
  </div>
</div>

