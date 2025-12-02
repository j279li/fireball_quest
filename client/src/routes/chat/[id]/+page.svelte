<script lang="ts">
  // Disable server-side rendering for this route to avoid SSR errors
  // referencing `window` while we fix the underlying server-side issue.
  export const ssr = false;
  import { PUBLIC_BACKEND_BASE } from "$env/static/public";
  import Button from "$lib/components/ui/button/button.svelte";
  import Input from "$lib/components/ui/input/input.svelte";
  import MessageItem from "../MessageItem.svelte";
  import { onMount, onDestroy, tick } from "svelte";
  import { page } from "$app/stores";
  import { UserPlus, AlertCircle, X } from "lucide-svelte";

  type WireMsg = {
    username: string;
    message: string | { message: string; tag?: string };
    avatarUrl?: string;
    tag?: string;
    ts?: number;
  };

  let ws: WebSocket;
  let scroller: HTMLDivElement;

  let messages = $state<
    {
      username: string;
      message: string;
      tag?: string;
      avatarUrl?: string;
      ts: number;
    }[]
  >([]);

  let text = $state("");

  // Invite modal state (invite lives inside chat)
  let inviteOpen = $state(false);
  let inviteUsername = $state("");
  let inviteError = $state("");
  let inviteLoading = $state(false);
  let showToast = $state(false);
  let toastMessage = $state("");

  type Tool = "image" | "note" | "roll" | "ooc" | "action" | null;
  let activeTool: Tool = $state(null);
  let hideOOC = $state(false);

  function toggleTool(t: Exclude<Tool, null>) {
    activeTool = activeTool === t ? null : t;
  }

  function toolToTag(t: Tool) {
    if (t === "ooc") return "OOC";
    if (t === "action") return "Action";
    if (t === "roll") return "Roll";
    return undefined;
  }

  function toolPlaceholder(t: Tool) {
    if (t === "action") return "Send battle message...";
    if (t === "ooc") return "Send OOC message...";
    if (t === "roll") return "Type roll command (coming soon)...";
    return "Coming soon...";
  }

  function decodeIncoming(raw: WireMsg) {
    if (typeof raw.message === "object")
      return { text: raw.message.message, tag: raw.message.tag ?? raw.tag };

    try {
      const parsed = JSON.parse(raw.message as string);
      if (parsed && typeof parsed === "object")
        return { text: parsed.message, tag: parsed.tag ?? raw.tag };
    } catch {
      // ignore JSON parse errors, treat as plain text
    }

    return { text: raw.message as string, tag: raw.tag };
  }

  onMount(() => {
    const token = localStorage.getItem("token");
    const chatId = $page.params.id; // ← get "1" from /chat/1

    ws = new WebSocket(
      PUBLIC_BACKEND_BASE.replace(/^http/, "ws") +
        "/chat/" + chatId + "?token=" +
        token
    );

    ws.onopen = () => {
      console.log("WS connected");
    };

    ws.onerror = (e) => {
      console.error("WebSocket error:", e);
    };

    ws.onclose = (e) => {
      console.warn("WebSocket closed:", e.code, e.reason);
    };

    ws.onmessage = (e) => {
      const raw = JSON.parse(e.data) as WireMsg;
      const { text, tag } = decodeIncoming(raw);

      messages = [
        ...messages,
        {
          username: raw.username,
          message: text,
          avatarUrl: raw.avatarUrl,
          tag,
          ts: raw.ts ?? Date.now()
        }
      ];
    };

    // Debug: capture DOM clicks at capture phase to check whether the
    // Invite button clicks reach the DOM (helps debug missing Svelte handlers).
    const _clickCapture = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null;
      try {
        if (typeof window !== 'undefined' && target && target.closest && target.closest('#invite-btn')) {
          console.log('DOM capture: click on #invite-btn', { target });
        }
      } catch {}
    };
    window.addEventListener('click', _clickCapture, true);

    // store listener so we can remove it on destroy
    (window as any).__invite_debug_listener = _clickCapture;
  });

  onDestroy(() => {
    if (ws?.readyState === WebSocket.OPEN) ws.close();
    if (typeof window !== 'undefined') {
      const l = (window as any).__invite_debug_listener;
      if (l) window.removeEventListener('click', l, true);
    }
  });

  function sendMessage(e?: Event) {
    try { e?.preventDefault?.(); } catch {}
    const payload = text.trim();
    if (!payload || ws?.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ message: payload, tag: toolToTag(activeTool) }));
    text = "";
  }

  function openInviteModal() {
    console.log("openInviteModal() called");
    inviteOpen = true;
    inviteUsername = "";
    inviteError = "";
    try { document.body.dataset.inviteOpen = '1'; } catch {}
    // After Svelte updates the DOM, check whether the modal element exists
    tick().then(() => {
      const el = typeof document !== 'undefined' && document.querySelector('[data-invite-modal]');
      console.log('openInviteModal: modal element present?', !!el, el);
      if (el) {
        // force visible for debugging
        try { (el as HTMLElement).style.zIndex = '99999'; } catch {}
      }
    });
  }

  function closeInviteModal() {
    if (inviteLoading) return;
    inviteOpen = false;
    inviteError = "";
  }

  async function invitePlayer() {
    inviteError = "";
    const campaignId = $page.params.id;

    if (!inviteUsername.trim()) {
      inviteError = "Please enter a username.";
      return;
    }

    // Authorization is optional on the client side; the server currently
    // accepts invite requests without authentication. Include a bearer
    // header only if the token exists, but always send the network request
    // so the button actually functions.
    const token = localStorage.getItem("token");

    console.log("invitePlayer() called", { inviteUsername, campaignId });
    inviteLoading = true;
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers.Authorization = `Bearer ${token}`;

      const res = await fetch(`${PUBLIC_BACKEND_BASE}/campaigns/${campaignId}/members`, {
        method: "POST",
        headers,
        body: JSON.stringify({ username: inviteUsername.trim() })
      });
      console.log("invitePlayer() fetch completed", { status: res.status });

      if (res.ok) {
        toastMessage = `Invited ${inviteUsername.trim()}`;
        showToast = true;
        setTimeout(() => (showToast = false), 3000);
        inviteOpen = false;
        inviteUsername = "";
      } else {
        let msg = "Could not invite user.";
        try {
          const data = await res.json();
          if (typeof data?.detail === "string") msg = data.detail;
        } catch {}
        inviteError = msg;
      }
      } catch (e) {
        console.error("Invite failed:", e);
        inviteError = "Something went wrong. Please try again.";
      } finally {
        inviteLoading = false;
      }
  }

  // auto-scroll to latest
  $effect(() => {
    void messages.length;
    tick().then(() => {
      if (scroller) scroller.scrollTop = scroller.scrollHeight;
    });
  });

</script>

<!-- PAGE ROOT: fills area, allows children to shrink -->
<div class="flex flex-col flex-1 min-h-0">
  <h1 class="text-2xl font-semibold mb-4 px-6 pt-6">
    Global Chat
  </h1>
  <div class="px-6 mb-4 flex items-center gap-3 h-12 min-h-12 shrink-0">
    <!-- Hide/show OOC messages toggle beside invite -->
    <button
      type="button"
      class="inline-flex items-center gap-2 rounded-md border border-slate-600 px-3 py-1 text-sm font-medium text-slate-300 bg-transparent hover:bg-slate-800"
      aria-pressed={hideOOC}
      onclick={() => (hideOOC = !hideOOC)}
      title={hideOOC ? 'Show OOC messages' : 'Hide OOC messages'}
    >
      {hideOOC ? 'Show OOC' : 'Hide OOC'}
    </button>

    {#if !inviteOpen}
      <button
        id="invite-btn"
        type="button"
        class="h-8 inline-flex items-center gap-2 rounded-md border border-slate-600 px-3 text-sm font-medium text-slate-300 bg-transparent hover:bg-slate-800 justify-center"
        onclick={() => { console.log('Invite button clicked'); openInviteModal(); }}
      >
        <UserPlus class="w-4 h-4 text-white" />
        <span>Invite Player</span>
      </button>
    {:else}
      <div class="inline-flex items-center gap-2">
        <Input
          bind:value={inviteUsername}
          placeholder="Player username"
          disabled={inviteLoading}
          height="h-7"
          class="h-7 py-1 text-sm border-slate-700"
          onkeydown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              invitePlayer();
            }
            if (e.key === 'Escape') {
              e.preventDefault();
              closeInviteModal();
            }
          }}
        />

        <button
          type="button"
          class="h-8 inline-flex items-center px-3 text-sm rounded-md bg-sky-600 hover:bg-sky-500 text-slate-50 justify-center"
          onclick={invitePlayer}
          disabled={inviteLoading}
        >
          {#if inviteLoading}
            Inviting…
          {:else}
            Invite
          {/if}
        </button>

        <button
          type="button"
          class="h-8 inline-flex items-center px-3 text-sm rounded-md border border-slate-600 text-slate-400 hover:bg-slate-800 justify-center"
          onclick={closeInviteModal}
          disabled={inviteLoading}
        >
          Cancel
        </button>
      </div>
    {/if}
  </div>

  <!-- Content block: shrinks, ONLY messages scroll -->
  <div class="flex flex-col flex-1 min-h-0 px-6 pb-6 gap-3">
    <!-- Messages: THIS is the ONLY scrollable element -->
    <div
      bind:this={scroller}
      class="flex-1 min-h-0 overflow-y-auto rounded-lg border bg-muted/30 p-4"
    >
      <ul class="space-y-4">
        {#each (hideOOC ? messages.filter(m => m.tag !== 'OOC') : messages) as m (m.ts + m.username + m.message)}
          <MessageItem {...m} />
        {/each}
      </ul>
    </div>

    <!-- Composer -->
    <form
      class="flex items-center gap-2 shrink-0"
      onsubmit={sendMessage}
    >
      <!-- TOOLBAR -->
      <div class="flex items-center gap-2 pr-2">
        <button
          type="button"
          aria-pressed={activeTool === "image"}
          onclick={() => toggleTool("image")}
          class="flex items-center justify-center h-9 w-9 rounded-md border transition
                 {activeTool === 'image'
                   ? 'bg-primary text-primary-foreground border-primary'
                   : 'bg-transparent text-muted-foreground hover:bg-accent'}"
          title="Image"
        >
          🖼️
        </button>

        <button
          type="button"
          aria-pressed={activeTool === "note"}
          onclick={() => toggleTool("note")}
          class="flex items-center justify-center h-9 w-9 rounded-md border transition
                 {activeTool === 'note'
                   ? 'bg-primary text-primary-foreground border-primary'
                   : 'bg-transparent text-muted-foreground hover:bg-accent'}"
          title="Note"
        >
          📄
        </button>

        <button
          type="button"
          aria-pressed={activeTool === "roll"}
          onclick={() => toggleTool("roll")}
          class="flex items-center justify-center h-9 w-9 rounded-md border transition
                 {activeTool === 'roll'
                   ? 'bg-primary text-primary-foreground border-primary'
                   : 'bg-transparent text-muted-foreground hover:bg-accent'}"
          title="Roll"
        >
          🎲
        </button>

        <button
          type="button"
          aria-pressed={activeTool === "ooc"}
          onclick={() => toggleTool("ooc")}
          class="h-9 px-3 rounded-md border transition
                 {activeTool === 'ooc'
                   ? 'bg-primary text-primary-foreground border-primary'
                   : 'bg-transparent text-muted-foreground hover:bg-accent'}"
          title="Out of Character"
        >
          OOC
        </button>

        <button
          type="button"
          aria-pressed={activeTool === "action"}
          onclick={() => toggleTool("action")}
          class="flex items-center gap-1 h-9 px-3 rounded-md border transition
                 {activeTool === 'action'
                   ? 'bg-primary text-primary-foreground border-primary'
                   : 'bg-transparent text-muted-foreground hover:bg-accent'}"
          title="Action"
        >
          ⚡ <span>Action</span>
        </button>
      </div>

      <Input
        bind:value={text}
        placeholder={toolPlaceholder(activeTool)}
        onkeydown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
          }
        }}
        autofocus
      />
      <Button type="submit">Send</Button>
    </form>
  </div>
  </div>
