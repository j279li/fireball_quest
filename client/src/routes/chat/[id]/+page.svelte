<script lang="ts">
  import { PUBLIC_BACKEND_BASE } from "$env/static/public";
  import Button from "$lib/components/ui/button/button.svelte";
  import Input from "$lib/components/ui/input/input.svelte";
  import MessageItem from "../MessageItem.svelte";
  import { onMount, onDestroy, tick } from "svelte";
  import { page } from "$app/stores";

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

  type Tool = "image" | "note" | "roll" | "ooc" | "action" | null;
  let activeTool: Tool = $state(null);

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
    if (t === "roll") return "Type roll command (e.g., 1d20+2)...";
    return "Type a message...";
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
  });

  onDestroy(() => {
    if (ws?.readyState === WebSocket.OPEN) ws.close();
  });

  function sendMessage() {
    const payload = text.trim();
    if (!payload || ws?.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ message: payload, tag: toolToTag(activeTool) }));
    text = "";
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

  <!-- Content block: shrinks, ONLY messages scroll -->
  <div class="flex flex-col flex-1 min-h-0 px-6 pb-6 gap-3">
    <!-- Messages: THIS is the ONLY scrollable element -->
    <div
      bind:this={scroller}
      class="flex-1 min-h-0 overflow-y-auto rounded-lg border bg-muted/30 p-4"
    >
      <ul class="space-y-4">
        {#each messages as m (m.ts + m.username + m.message)}
          <MessageItem {...m} />
        {/each}
      </ul>
    </div>

    <!-- Composer -->
    <form
      class="flex items-center gap-2 shrink-0"
      on:submit|preventDefault={sendMessage}
    >
      <!-- TOOLBAR -->
      <div class="flex items-center gap-2 pr-2">
        <button
          type="button"
          aria-pressed={activeTool === "image"}
          on:click={() => toggleTool("image")}
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
          on:click={() => toggleTool("note")}
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
          on:click={() => toggleTool("roll")}
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
          on:click={() => toggleTool("ooc")}
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
          on:click={() => toggleTool("action")}
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
        on:keydown={(e) => {
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
