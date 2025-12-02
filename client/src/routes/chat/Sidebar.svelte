<script lang="ts">
  import { ScrollArea } from "$lib/components/ui/scroll-area";
  import { Separator } from "$lib/components/ui/separator";
  import { Button } from "$lib/components/ui/button";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { PUBLIC_BACKEND_BASE } from "$env/static/public";

  import SidebarCharacter from "./SidebarCharacter.svelte";
  import SidebarSpells from "./SidebarSpells.svelte";

  $: url = $page.url;
  // read selection from query param; default to notes
  $: active = (url.searchParams.get("panel") ?? "notes") as "character" | "spells" | "items" | "notes";

  type Link = { id: "character" | "spells" | "items" | "notes"; label: string; icon: string; disabled?: boolean };
  const links: Link[] = [
    { id: "character", label: "Character", icon: "👤", disabled: true },
    { id: "spells",    label: "Spells",    icon: "⚡", disabled: true },
    { id: "items",     label: "Items",     icon: "📦" },
    { id: "notes",     label: "Notes",     icon: "📝" },
  ];

  function setPanel(id: typeof links[number]["id"]) {
    // update URL without full reload or scroll jump; keeps back/forward history tidy
    const next = new URL(url);
    next.searchParams.set("panel", id);
    goto(next, { replaceState: false, noScroll: true, keepFocus: true });
  }

  const isActive = (id: string) => active === id;

  let campaignName: string | null = null;

  // Fetch campaign name for current chat (param may be a campaign id or a session id)
  onMount(async () => {
    const id = $page.params.id;
    if (!id) return;
    const token = localStorage.getItem("token");

    try {
      const headers: Record<string, string> = {};
      if (token) headers.Authorization = `Bearer ${token}`;

      // Try fetching campaigns the user has access to and match by id
      const res = await fetch(`${PUBLIC_BACKEND_BASE}/campaigns`, { headers });
      if (res.ok) {
        const campaigns = await res.json();
        const match = campaigns.find((c: any) => String(c.id) === String(id));
        if (match) {
          campaignName = match.name ?? null;
          return;
        }
      }

      // Fallback: if id is a session id, fetch sessions and resolve its campaign_id
      const sres = await fetch(`${PUBLIC_BACKEND_BASE}/sessions`, { headers });
      if (sres.ok) {
        const sessions = await sres.json();
        const session = sessions.find((s: any) => String(s.id) === String(id));
        if (session && session.campaign_id) {
          // refetch campaigns to find campaign name
          const r2 = await fetch(`${PUBLIC_BACKEND_BASE}/campaigns`, { headers });
          if (r2.ok) {
            const campaigns2 = await r2.json();
            const match2 = campaigns2.find((c: any) => c.id === session.campaign_id);
            if (match2) campaignName = match2.name ?? null;
          }
        }
      }
    } catch (e) {
      console.error('Failed to load campaign name for sidebar', e);
    }
  });
</script>

<div class="flex h-full flex-col">
  <!-- Header (fixed) -->
  <div class="p-4 pb-3 shrink-0">
    <a href="/home" class="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
      ← <span>Back to Home</span>
    </a>
    <h1 class="mt-3 text-lg font-semibold leading-tight">
      {campaignName ?? 'Campaign'}
    </h1>
    <div class="mt-2 flex items-center gap-2">
      <span class="h-2.5 w-2.5 rounded-full bg-green-500"></span>
      <span class="text-sm text-muted-foreground">2 Online</span>
    </div>
  </div>

  <Separator class="shrink-0" />

  <!-- Scrollable body (nav + dynamic panel) -->
  <ScrollArea class="flex-1 min-h-0 px-2">
    <!-- nav -->
    <nav class="mt-3 space-y-1">
      {#each links as link}
        <button
          type="button"
          on:click={() => !link.disabled && setPanel(link.id)}
          disabled={link.disabled}
          class={`w-full text-left flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
                  ${isActive(link.id)
                    ? "bg-accent text-accent-foreground shadow-sm"
                    : "text-foreground/90 hover:bg-accent hover:text-accent-foreground"}
                  ${link.disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
        >
          <span>{link.icon}</span>
          <span>{link.label}{link.disabled ? ' (WIP)' : ''}</span>
        </button>
      {/each}
    </nav>

    <Separator class="my-4" />

    <!-- dynamic panel -->
    {#if active === "character"}
      <SidebarCharacter />
    {:else if active === "spells"}
      <SidebarSpells />
    {:else if active === "items"}
      <div class="p-3 text-sm text-muted-foreground">Items panel coming soon…</div>
    {:else}
      <div class="p-3 text-sm text-muted-foreground">Notes panel coming soon…</div>
    {/if}
  </ScrollArea>

  <Separator class="shrink-0" />

  <!-- Footer (fixed) -->
  <div class="p-4 shrink-0">
    <Button class="w-full" variant="secondary">+ New Channel</Button>
  </div>
</div>
