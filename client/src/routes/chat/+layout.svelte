<script lang="ts">
  export let data;
  import Sidebar from "./Sidebar.svelte";
</script>

<!-- This sits inside the root layout's <main> -->
<div class="flex h-full overflow-hidden">
  <!-- Left: sidebar -->
  <aside class="w-64 shrink-0 border-r bg-background h-full overflow-y-auto">
    <Sidebar />
  </aside>

  <!-- Right: route content (chat) -->
  <main class="flex-1 min-w-0 flex flex-col overflow-hidden">
    <slot />
  </main>

   <!-- <aside class="w-64 shrink-0 border-r bg-background h-full overflow-y-auto">
    <Sidebar />
  </aside> -->
</div>
