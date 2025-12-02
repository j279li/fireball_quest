<script lang="ts">
  import Avatar from "$lib/components/ui/avatar/avatar.svelte";
  import AvatarImage from "$lib/components/ui/avatar/avatar-image.svelte";
  import AvatarFallback from "$lib/components/ui/avatar/avatar-fallback.svelte";
  import Badge from "$lib/components/ui/badge/badge.svelte";

  export let username = "";
  export let message = "";
  export let ts: number | Date = Date.now();
  export let avatarUrl: string | undefined = undefined;
  export let tag: string | undefined = undefined;

  const time = new Date(ts);
  const timeStr = Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit"
  }).format(time);

  const initials =
    username
      .split(/\s+/)
      .map((p) => p[0]?.toUpperCase())
      .slice(0, 2)
      .join("") || "?";
</script>

<li class="flex gap-3 items-start">
  <!-- Avatar -->
  <Avatar class="h-10 w-10 shrink-0 mt-1">
    <AvatarImage src={avatarUrl} alt={username} />
    <AvatarFallback>{initials}</AvatarFallback>
  </Avatar>

  <!-- Right side -->
  <div class="flex flex-col w-full min-w-0">
    <div class="flex items-center gap-2">
      <span class="font-semibold text-sm text-foreground">{username}</span>
      <span class="text-xs text-muted-foreground">{timeStr}</span>
      {#if tag && tag != "chat"}
        <Badge variant="secondary" class="px-2 py-0 h-5 text-[11px]">{tag}</Badge>
      {/if}
    </div>

    <div
      class="mt-1 rounded-lg border bg-card text-card-foreground shadow-sm px-3 py-2 text-[15px] leading-relaxed"
    >
      {message}
    </div>
  </div>
</li>
