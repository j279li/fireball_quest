<script lang="ts">
  import '../app.css';
  import favicon from '$lib/assets/favicon.svg';
  import Button from "$lib/components/ui/button/button.svelte";
  import { page } from "$app/state";
  import { jwtDecode } from "jwt-decode";
  import { onMount } from "svelte";
  import { username } from '$lib/test.ts';

  let { children } = $props();

  // Get username from token on mount
  onMount(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const decoded: any = jwtDecode(token);
        const name = decoded?.username ?? decoded?.sub ?? decoded?.name ?? null;
        username.set(name);
      } catch (e) {
        username.set(null);
      }
    } else {
      username.set(null);
    }
  });

  function handleStorage(e: StorageEvent) {
    if (e.key === 'token') {
      const token = e.newValue;
      if (token) {
        try {
          const decoded: any = jwtDecode(token);
          const name = decoded?.username ?? decoded?.sub ?? decoded?.name ?? null;
          username.set(name);
        } catch {
          username.set(null);
        }
      } else {
        username.set(null);
      }
    }
  }

  onMount(() => {
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  });
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<!-- ROOT: nav + content, exactly one h-screen -->
<div class="flex flex-col h-screen overflow-hidden">
  <!-- NAV BAR -->
  <nav class="border-b border-gray-200 bg-white p-4 flex justify-between shrink-0">
    <div class="flex gap-4">
      <a href="/" class="font-semibold" class:underline={page.url.pathname === '/home'}>Home</a>
      <!-- <a href="/chat" class="font-semibold" class:underline={page.url.pathname === '/chat'}>Chat</a> -->
      <!-- <a href="/login" class="font-semibold" class:underline={page.url.pathname === '/login'}>Login</a> -->
    {#if !$username}
  <a href="/login" class="font-semibold" class:underline={page.url.pathname === '/login'}>
    Login
  </a>
{/if}

	</div>
   {#if $username}
  <div class="text-sm text-muted-foreground">
    Logged in as:
    <a
      href="/login"
      class="font-medium text-foreground hover:underline cursor-pointer"
    >
      {$username}
    </a>
  </div>
{/if}
  </nav>

  <!-- Content below nav fills remaining height -->
  <main class="flex-1 min-h-0 overflow-hidden">
    {@render children?.()}
  </main>
</div>
