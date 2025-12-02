<script lang="ts">
  import { Input } from "$lib/components/ui/input";
  import { Separator } from "$lib/components/ui/separator";
  import { Button } from "$lib/components/ui/button";
  import { createEventDispatcher } from "svelte";

  const dispatch = createEventDispatcher();

  // Example props (replace with your data/store later)
  export type Item = {
    id: string;
    name: string;
    qty: number;
    weight?: number;   // optional (lbs)
    type?: string;     // e.g., "Weapon", "Potion", "Gear"
  };

  export let items: Item[] = [
    { id: "potion-heal", name: "Potion of Healing", qty: 2, type: "Potion", weight: 0.5 },
    { id: "rope-hemp",  name: "Hemp Rope (50 ft)",  qty: 1, type: "Gear",   weight: 10 },
    { id: "shortsword", name: "Shortsword",         qty: 1, type: "Weapon", weight: 2 },
  ];

  let q = "";
  let filter: string | null = null; // category filter; null = all

  $: categories = Array.from(new Set(items.map(i => i.type).filter(Boolean))) as string[];

  $: filtered = items
    .filter(i => !filter || i.type === filter)
    .filter(i => q ? i.name.toLowerCase().includes(q.trim().toLowerCase()) : true);

  function inc(id: string) {
    const i = items.find(x => x.id === id);
    if (!i) return;
    i.qty += 1;
    items = [...items];
    dispatch("change", { items });
  }

  function dec(id: string) {
    const i = items.find(x => x.id === id);
    if (!i) return;
    i.qty = Math.max(0, i.qty - 1);
    items = [...items];
    dispatch("change", { items });
  }

  function remove(id: string) {
    items = items.filter(x => x.id !== id);
    dispatch("change", { items });
  }

  function addQuick() {
    // placeholder UX – replace with modal/sheet later
    const id = `new-${crypto.randomUUID().slice(0, 8)}`;
    const item = { id, name: "New Item", qty: 1, type: "Gear", weight: 1 };
    items = [item, ...items];
    dispatch("add", { item, items });
  }
</script>

<!-- Title -->
<h2 class="px-3 text-sm font-medium text-muted-foreground">Items</h2>

<div class="p-3 space-y-3 text-sm">
  <!-- Filters -->
  <div class="grid grid-cols-2 gap-2">
    <Input placeholder="Search items…" bind:value={q} class="h-8" />
    <div class="flex items-center gap-1">
      <button
        type="button"
        class={`flex-1 rounded-md border px-2 py-1 text-xs
                ${filter === null ? "bg-accent text-accent-foreground" : "hover:bg-accent/50"}`}
        on:click={() => (filter = null)}
      >
        All
      </button>

      {#each categories as c}
        <button
          type="button"
          class={`flex-1 rounded-md border px-2 py-1 text-xs
                  ${filter === c ? "bg-accent text-accent-foreground" : "hover:bg-accent/50"}`}
          on:click={() => (filter = c)}
        >
          {c}
        </button>
      {/each}
    </div>
  </div>

  <Separator />

  <!-- Inventory list -->
  <div class="rounded-md border bg-background">
    {#if filtered.length === 0}
      <p class="px-3 py-2 text-xs text-muted-foreground">No items.</p>
    {:else}
      <ul class="divide-y">
        {#each filtered as it}
          <li class="flex items-center gap-2 px-3 py-2">
            <button
              type="button"
              class="flex-1 truncate text-left"
              title={it.name}
              on:click={() => dispatch("openItem", it)}  
            >
              <span class="font-medium">{it.name}</span>
              {#if it.type}
                <span class="ml-1 text-[10px] text-muted-foreground">({it.type})</span>
              {/if}
              {#if it.weight != null}
                <span class="ml-2 text-[10px] text-muted-foreground">{it.weight} lb</span>
              {/if}
            </button>

            <div class="flex items-center gap-1">
              <Button variant="secondary" size="sm" class="h-6 px-2" on:click={() => dec(it.id)}>–</Button>
              <span class="w-6 text-center text-xs">{it.qty}</span>
              <Button variant="secondary" size="sm" class="h-6 px-2" on:click={() => inc(it.id)}>+</Button>
            </div>

            <button
              type="button"
              class="ml-1 rounded-md border px-2 py-0.5 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              on:click={() => remove(it.id)}
              aria-label="Remove item"
              title="Remove"
            >
              remove
            </button>
          </li>
        {/each}
      </ul>
    {/if}
  </div>

  <!-- Quick add -->
  <div class="flex items-center justify-between">
    <span class="text-xs text-muted-foreground">Add an item</span>
    <Button size="sm" variant="secondary" class="h-7 px-2" on:click={addQuick}>+ Add</Button>
  </div>
</div>

<Separator class="mt-3" />
