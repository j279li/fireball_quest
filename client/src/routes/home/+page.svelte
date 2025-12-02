<script lang="ts">
  import { PUBLIC_BACKEND_BASE } from "$env/static/public";
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { username } from "$lib/test.ts";

  import { Button } from "$lib/components/ui/button";
  import {
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
    CardFooter
  } from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { Input } from "$lib/components/ui/input";

  import {
    Users,
    Clock,
    CalendarDays,
    Play,
    CheckCircle2,
    UserPlus,
    X,
    AlertCircle,
    CheckCircle2 as CheckIcon
  } from "lucide-svelte";

  type Campaign = {
    id: number;
    name: string;
    game_system_id: number;
    created_at: string;
  };

  type SessionSummary = {
    id: number;
    name: string;
    campaign_name?: string;
    scheduled_at?: string | null;
    last_played_at?: string | null;
    player_count?: number | null;
    status?: string | null;
    completed?: boolean;
  };

  let loading = true;
  let ownedCampaigns: Campaign[] = [];
  let sessions: SessionSummary[] = [];
  let isGM = false;
  let currentCampaignId: number | null = null;


  let createSessionOpen = false;
  let createName = "";
  let createScheduledAt = "";
  let createSessionError = "";
  let createSessionLoading = false;

  async function loadSessions(token: string) {
  try {
    const sessionsRes = await fetch(`${PUBLIC_BACKEND_BASE}/sessions`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    if (sessionsRes.ok) {
      const d = await sessionsRes.json();
      const rawSessions = Array.isArray(d)
        ? d
        : Array.isArray(d.sessions)
        ? d.sessions
        : [];
      sessions = rawSessions.map(normalizeSession);
    } else {
      sessions = [];
    }
  } catch (err) {
    console.error("Failed to load sessions:", err);
    sessions = [];
  }
}

function openCreateSessionModal() {
  createSessionOpen = true;
  createName = "";
  createScheduledAt = "";
  createSessionError = "";
}

function closeCreateSessionModal() {
  if (createSessionLoading) return;
  createSessionOpen = false;
  createSessionError = "";
}

async function createSession() {
  createSessionError = "";

  if (!createName.trim()) {
    createSessionError = "Please enter a session name.";
    return;
  }

  const token = localStorage.getItem("token");
  if (!token) {
    createSessionError = "You must be logged in.";
    return;
  }

  createSessionLoading = true;
  try {
    const res = await fetch(`${PUBLIC_BACKEND_BASE}/sessions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        campaign_id: 1, // hardcoded for now
        name: createName.trim(),
        scheduled_at: createScheduledAt || null
      })
    });

    if (res.ok) {
      // refresh sessions list
      await loadSessions(token);

      // optional toast (reusing your existing toast state)
      toastMessage = `Session "${createName.trim()}" created.`;
      showToast = true;
      setTimeout(() => {
        showToast = false;
      }, 3000);

      // close modal
      createSessionOpen = false;
      createName = "";
      createScheduledAt = "";
      createSessionError = "";
    } else {
      let msg = "Could not create session.";
      try {
        const data = await res.json();
        if (typeof data?.detail === "string") msg = data.detail;
      } catch {
        /* ignore */
      }
      createSessionError = msg;
    }
  } catch (e) {
    console.error("Create session failed:", e);
    createSessionError = "Something went wrong. Please try again.";
  } finally {
    createSessionLoading = false;
  }
}

  // Normalize backend sessions
  function normalizeSession(raw: any): SessionSummary {
    return {
      id: raw?.id ?? Math.random(),
      name: raw?.name ?? "Untitled Session",
      campaign_name: raw?.campaign_name ?? raw?.campaign ?? "Unknown Campaign",
      scheduled_at: raw?.scheduled_at ?? null,
      last_played_at: raw?.created_at ?? null,
      player_count:
        typeof raw?.player_count === "number" ? raw.player_count : null,
      status: raw?.status ?? null,
      completed: raw?.ended_at == null
    };
  }

  // Members in campaign
  let members: { username: string }[] = [];
  let membersLoading = true;

  async function loadMembers(token: string, campaignId: number) {
    try {
      const res = await fetch(
        `${PUBLIC_BACKEND_BASE}/campaign/${campaignId}/members`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (res.ok) {
        const d = await res.json();
        members = Array.isArray(d) ? d : d.members ?? [];
      } else {
        members = [];
      }
    } catch (e) {
      console.error("Failed to load members:", e);
      members = [];
    } finally {
      membersLoading = false;
    }
  }

  // Invite Player modal state
  let inviteOpen = false;
  let inviteUsername = "";
  let inviteError = "";
  let inviteLoading = false;

  // Simple local toast
  let showToast = false;
  let toastMessage = "";

  function openInviteModal() {
	console.log("openInviteModal called");
    inviteOpen = true;
    inviteUsername = "";
    inviteError = "";
  }

  function closeInviteModal() {
    if (inviteLoading) return;
    inviteOpen = false;
    inviteError = "";
  }

  async function invitePlayer() {
    inviteError = "";

    if (!inviteUsername.trim()) {
      inviteError = "Please enter a username.";
      return;
    }

    if (!currentCampaignId) {
      inviteError = "No active campaign found.";
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      inviteError = "You must be logged in.";
      return;
    }

    inviteLoading = true;
    try {
      const res = await fetch(
        `${PUBLIC_BACKEND_BASE}/campaigns/1/invite/${encodeURIComponent(
          inviteUsername.trim()
        )}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ campaign_id: currentCampaignId })
        }
      );

      if (res.ok) {
        // refresh members
        membersLoading = true;
        await loadMembers(token, currentCampaignId);

        // show toast
        toastMessage = `Player "${inviteUsername.trim()}" has been invited.`;
        showToast = true;
        setTimeout(() => {
          showToast = false;
        }, 3000);

        // close modal
        inviteOpen = false;
        inviteUsername = "";
        inviteError = "";
      } else {
        // try to read server error message, fall back to generic
        let msg = "User not found.";
        try {
          const data = await res.json();
          if (typeof data?.detail === "string") msg = data.detail;
        } catch {
          /* ignore parse error */
        }
        inviteError = msg;
      }
    } catch (e) {
      console.error("Invite failed:", e);
      inviteError = "Something went wrong. Please try again.";
    } finally {
      inviteLoading = false;
    }
  }

  // Derived slices for GM dashboard
  $: activeSessions = sessions.slice(0, 2);
  $: recentSessions = sessions.slice(2);

  onMount(async () => {
    const token = localStorage.getItem("token");
    if (!token) {
	goto("/login");
      loading = false;
      return;
    }

    try {
      // 1) Is user a GM? (owns any campaigns)
      const ownedRes = await fetch(`${PUBLIC_BACKEND_BASE}/campaigns/owned`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (ownedRes.ok) {
        const d = await ownedRes.json();
        ownedCampaigns = Array.isArray(d)
          ? d
          : Array.isArray(d.campaigns)
          ? d.campaigns
          : [];
      } else {
        ownedCampaigns = [];
      }

      isGM = ownedCampaigns.length > 0;

      if (ownedCampaigns.length > 0) {
        currentCampaignId = ownedCampaigns[0].id;
        await loadMembers(token, currentCampaignId);
      }

	   await loadSessions(token);
    //   // 2) Sessions current user is in
    //   const sessionsRes = await fetch(`${PUBLIC_BACKEND_BASE}/sessions`, {
    //     headers: { Authorization: `Bearer ${token}` }
    //   });

    //   if (sessionsRes.ok) {
    //     const d = await sessionsRes.json();
    //     const rawSessions = Array.isArray(d)
    //       ? d
    //       : Array.isArray(d.sessions)
    //       ? d.sessions
    //       : [];
    //     sessions = rawSessions.map(normalizeSession);
    //   } else {
    //     sessions = [];
    //   }

      // 3) If non-GM but has sessions, go straight to /chat/{firstSessionId}
      if (!isGM && sessions.length > 0) {
        goto(`/chat/${sessions[0].id}`);
        return;
      }
    } catch (err) {
      console.error("Error loading home data:", err);
      ownedCampaigns = [];
      sessions = [];
      isGM = false;
    } finally {
      loading = false;
    }
  });

  // Helper labels with safe fallbacks
  function sessionStatusLabel(s: SessionSummary, fallback: string) {
    return s.status ?? fallback ?? "Status Unknown";
  }

  function sessionLastPlayedLabel(s: SessionSummary) {
    if (!s.last_played_at) return "Unknown time";

    const date = new Date(s.last_played_at);

    return date.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit"
    });
  }

  function sessionTimeLabel(s: SessionSummary) {
    if (!s.scheduled_at)
		return "No scheduled time";
	const date = new Date(s.scheduled_at);

    return "Scheduled: " + date.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit"
    });
  }

  function sessionPlayersLabel(s: SessionSummary) {
    if (s.player_count != null) return `${s.player_count} players`;
    return "Players: 3";
  }
</script>

<!-- DARK ROOT: high-contrast, readable -->
<div class="flex h-full flex-col bg-slate-900 text-slate-50 overflow-y-auto">
  {#if loading}
    <div class="flex flex-1 items-center justify-center">
      <p class="text-sm text-slate-300">Loading your campaigns…</p>
    </div>

  {:else if isGM}
    <!-- ===================== -->
    <!--       GM DASHBOARD    -->
    <!-- ===================== -->
    <div class="relative max-w-6xl mx-auto w-full py-8 px-6 space-y-10">
      <!-- Toast -->
      {#if showToast}
        <div class="fixed right-4 top-20 z-50">
          <div class="flex items-center gap-2 rounded-lg bg-emerald-600/90 px-4 py-2 shadow-lg border border-emerald-400/70">
            <CheckIcon class="w-4 h-4 text-emerald-50" />
            <span class="text-sm text-emerald-50">{toastMessage}</span>
          </div>
        </div>
      {/if}

      <!-- Header -->
      <header class="flex items-center justify-between gap-4">
        <div>
          <h1 class="text-3xl font-semibold tracking-tight text-slate-50">
            Fireball.quest
          </h1>
          <p class="text-sm text-slate-300">
            Your RPG campaigns and sessions.
          </p>
        </div>

        <div class="flex items-center gap-3">
              <button
				type="button"
				class="inline-flex items-center gap-2 rounded-md bg-sky-600 px-3 py-2 text-sm font-medium text-slate-50 shadow-sm hover:bg-sky-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
				on:click={openCreateSessionModal}
				>
				+ New Session
				</button>
         <button
			type="button"
			class="inline-flex items-center gap-2 rounded-md border border-sky-500/70 px-3 py-2 text-sm font-medium text-sky-300 bg-transparent hover:bg-sky-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
			on:click={openInviteModal}
			>
			<UserPlus class="w-4 h-4" />
			<span>Invite Player</span>
			</button>
        </div>
      </header>

      <!-- Players Box -->
      <div class="mt-4 bg-slate-800 border border-slate-700 rounded-lg p-4 shadow-md">
        <h3 class="text-lg font-semibold text-slate-50 mb-2 flex items-center gap-2">
          <Users class="w-5 h-5 text-sky-400" />
          Players in Your Campaign
        </h3>

        {#if membersLoading}
          <p class="text-slate-400 text-sm italic">Loading players...</p>
        {:else if members.length === 0}
          <p class="text-slate-400 text-sm italic">No players have joined yet.</p>
        {:else}
          <ul class="space-y-1">
            {#each members as m}
              <li class="text-slate-200 flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
                {m}
              </li>
            {/each}
          </ul>
        {/if}
      </div>

      <!-- Active Sessions -->
      <section class="space-y-4">
        <h2 class="text-xl font-semibold text-slate-50">Active Sessions</h2>

        {#if activeSessions.length === 0}
          <p class="text-sm text-slate-400">
            You don’t have any active sessions yet. Create one to get started.
          </p>
        {:else}
          <div class="grid gap-6 md:grid-cols-2">
            {#each activeSessions as s}
              <Card class="bg-slate-800 border-slate-700 shadow-sm flex flex-col text-slate-50">
                <CardHeader class="flex flex-row items-start justify-between gap-4 pb-3">
                  <div>
                    <CardTitle class="text-lg text-slate-50">
                      {s.name}
                    </CardTitle>
                    <CardDescription class="text-sm text-slate-300">
                      {s.campaign_name ?? "Campaign"}
                    </CardDescription>
                  </div>

                  <Badge
                    variant="outline"
                    class="border-emerald-400/70 text-emerald-200 bg-emerald-500/15"
                  >
                    {sessionStatusLabel(s, "Active")}
                  </Badge>
                </CardHeader>

                <CardContent class="space-y-3 text-sm text-slate-200">
                  <div class="flex items-center gap-4 text-xs text-slate-300">
                    <div class="flex items-center gap-1.5">
                      <Users class="w-4 h-4" />
                      <span>{sessionPlayersLabel(s)}</span>
                    </div>
                    <div class="flex items-center gap-1.5">
                      <Clock class="w-4 h-4" />
                      <span>{sessionLastPlayedLabel(s)}</span>
                    </div>
                  </div>

                  <div class="flex items-center gap-2 text-sm text-slate-200">
                    <CalendarDays class="w-4 h-4" />
                    <span>{sessionTimeLabel(s)}</span>
                  </div>
                </CardContent>

                <CardFooter class="mt-auto pt-2">
                  <button
                    type="button"
                    class="inline-flex w-full items-center justify-center gap-2 rounded-md bg-sky-600 px-3 py-2 text-sm font-medium text-slate-50 shadow-sm hover:bg-sky-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
                    on:click={() => goto(`/chat/${s.id}`)}
                  >
                    <Play class="w-4 h-4" />
                    <span>Continue Session</span>
                  </button>
                </CardFooter>
              </Card>
            {/each}
          </div>
        {/if}
      </section>

      <!-- Recent Sessions -->
      <section class="space-y-4 pb-6">
        <h2 class="text-xl font-semibold text-slate-50">Recent Sessions</h2>

        {#if recentSessions.length === 0}
          <p class="text-sm text-slate-400">
            When you wrap up sessions, they’ll show up here.
          </p>
        {:else}
          <Card class="bg-slate-800 border-slate-700 text-slate-50">
            <CardContent class="p-0 divide-y divide-slate-700/80">
              {#each recentSessions as s}
                <button
                  type="button"
                  class="flex w-full items-center justify-between px-5 py-4 text-left hover:bg-slate-700/70 transition-colors"
                  on:click={() => goto(`/chat/${s.id}`)}
                >
                  <div>
                    <div class="font-medium text-slate-50">{s.name}</div>
                    <div class="text-xs text-slate-300">
                      {s.campaign_name ?? "Campaign"}
                    </div>
                  </div>

                  <div class="flex items-center gap-6 text-xs text-slate-300">
                    <div class="flex items-center gap-1.5">
                      <Users class="w-4 h-4" />
                      <span>{sessionPlayersLabel(s)}</span>
                    </div>
                    <div class="flex items-center gap-1.5">
                      <Clock class="w-4 h-4" />
                      <span>{sessionLastPlayedLabel(s)}</span>
                    </div>
                    <Badge
                      variant="outline"
                      class="flex items-center gap-1 border-slate-600 text-slate-100 bg-slate-900"
                    >
                      <CheckCircle2 class="w-3 h-3" />
                      <span>{sessionStatusLabel(s, "Completed")}</span>
                    </Badge>
                  </div>
                </button>
              {/each}
            </CardContent>
          </Card>
        {/if}
      </section>

      <!-- Invite Player Modal -->
      {#if inviteOpen}
        <div class="fixed inset-0 z-40 flex items-center justify-center bg-black/60">
          <div class="w-full max-w-md rounded-xl bg-slate-900 border border-slate-700 shadow-2xl">
            <div class="flex items-center justify-between px-4 py-3 border-b border-slate-700">
              <div class="flex items-center gap-2">
                <div class="inline-flex h-8 w-8 items-center justify-center rounded-full bg-sky-600/20">
                  <UserPlus class="w-4 h-4 text-sky-300" />
                </div>
                <div>
                  <h2 class="text-sm font-semibold text-slate-50">Invite Player</h2>
                  <p class="text-xs text-slate-400">
                    Add a player to your campaign by username.
                  </p>
                </div>
              </div>
              <button
                type="button"
                class="rounded-full p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-100"
                on:click={closeInviteModal}
                aria-label="Close"
              >
                <X class="w-4 h-4" />
              </button>
            </div>

            <div class="px-4 py-4 space-y-3">
              <div class="space-y-1.5">
                <label class="text-xs font-medium text-slate-200">
                  Player username
                </label>
                <Input
                  placeholder="e.g. JohnDoe"
                  bind:value={inviteUsername}
                  disabled={inviteLoading}
                  class="bg-slate-900 border-slate-700 text-slate-50 placeholder:text-slate-500"
                  on:keydown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      invitePlayer();
                    }
                  }}
                />
                <p class="text-[11px] text-slate-400">
                  This should match the username the player uses to log in.
                </p>
              </div>

              {#if inviteError}
                <div class="flex items-center gap-2 text-xs text-red-400">
                  <AlertCircle class="w-4 h-4" />
                  <span>{inviteError}</span>
                </div>
              {/if}
            </div>

            <div class="flex items-center justify-end gap-2 px-4 py-3 border-t border-slate-700 bg-slate-900/80">
		<button
  type="button"
  class="px-3 py-2 rounded-md border border-slate-600 text-slate-400 
         hover:bg-slate-800 hover:text-slate-200 transition-colors 
         disabled:opacity-50 disabled:cursor-not-allowed"
  on:click={closeInviteModal}
  disabled={inviteLoading}
>
  Cancel
</button>

              <button
  type="button"
  class="px-3 py-2 rounded-md bg-sky-600 hover:bg-sky-500 text-slate-50 
         inline-flex items-center gap-2 shadow-sm 
         disabled:opacity-50 disabled:cursor-not-allowed"
  on:click={invitePlayer}
  disabled={inviteLoading}
>
  {#if inviteLoading}
    <span class="h-3 w-3 rounded-full border-2 border-slate-200 border-t-transparent animate-spin"></span>
    <span>Inviting…</span>
  {:else}
    <UserPlus class="w-4 h-4" />
    <span>Invite</span>
  {/if}
</button>
            </div>
          </div>
        </div>
      {/if}

	  {#if createSessionOpen}
		<div class="fixed inset-0 z-40 flex items-center justify-center bg-black/60">
			<div class="w-full max-w-md rounded-xl bg-slate-900 border border-slate-700 shadow-2xl">
			<!-- Header -->
			<div class="flex items-center justify-between px-4 py-3 border-b border-slate-700">
				<div class="flex items-center gap-2">
				<div class="inline-flex h-8 w-8 items-center justify-center rounded-full bg-sky-600/20">
					<CalendarDays class="w-4 h-4 text-sky-300" />
				</div>
				<div>
					<h2 class="text-sm font-semibold text-slate-50">Create Session</h2>
					<p class="text-xs text-slate-400">
					Set up a new session for your campaign.
					</p>
				</div>
				</div>
				<button
				type="button"
				class="rounded-full p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-100"
				on:click={closeCreateSessionModal}
				aria-label="Close"
				>
				<X class="w-4 h-4" />
				</button>
			</div>

			<!-- Body -->
			<div class="px-4 py-4 space-y-4">
				<div class="space-y-1.5">
				<label class="text-xs font-medium text-slate-200">
					Session name
				</label>
				<Input
					placeholder="e.g. Goblins at the Gate"
					bind:value={createName}
					disabled={createSessionLoading}
					class="bg-slate-900 border-slate-700 text-slate-50 placeholder:text-slate-500"
					on:keydown={(e) => {
					if (e.key === "Enter") {
						e.preventDefault();
						createSession();
					}
					}}
				/>
				</div>

				<div class="space-y-1.5">
				<label class="text-xs font-medium text-slate-200">
					Scheduled time <span class="text-slate-500">(optional)</span>
				</label>
				<input
					type="datetime-local"
					class="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-50 placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 disabled:opacity-50"
					bind:value={createScheduledAt}
					disabled={createSessionLoading}
				/>
				<p class="text-[11px] text-slate-400">
					Leave blank if you haven't scheduled it yet.
				</p>
				</div>

				{#if createSessionError}
				<div class="flex items-center gap-2 text-xs text-red-400">
					<AlertCircle class="w-4 h-4" />
					<span>{createSessionError}</span>
				</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="flex items-center justify-end gap-2 px-4 py-3 border-t border-slate-700 bg-slate-900/80">
				<button
				type="button"
				class="px-3 py-2 rounded-md border border-slate-600 text-slate-400 
						hover:bg-slate-800 hover:text-slate-200 transition-colors 
						disabled:opacity-50 disabled:cursor-not-allowed"
				on:click={closeCreateSessionModal}
				disabled={createSessionLoading}
				>
				Cancel
				</button>

				<button
				type="button"
				class="px-3 py-2 rounded-md bg-sky-600 hover:bg-sky-500 text-slate-50 
						inline-flex items-center gap-2 shadow-sm 
						disabled:opacity-50 disabled:cursor-not-allowed"
				on:click={createSession}
				disabled={createSessionLoading}
				>
				{#if createSessionLoading}
					<span class="h-3 w-3 rounded-full border-2 border-slate-200 border-t-transparent animate-spin"></span>
					<span>Creating…</span>
				{:else}
					<CalendarDays class="w-4 h-4" />
					<span>Create Session</span>
				{/if}
				</button>
			</div>
			</div>
		</div>
		{/if}


    </div>

  {:else}
    <!-- =========================================== -->
    <!-- NON-GM, NOT IN ANY SESSION / CAMPAIGN       -->
    <!-- =========================================== -->
    <div class="flex flex-1 items-center justify-center px-6">
      <Card class="w-full max-w-md bg-slate-800 border-slate-700 shadow-xl text-slate-50">
        <CardHeader>
          <CardTitle class="text-lg text-slate-50">
            You’re not in a campaign yet
          </CardTitle>
          <CardDescription class="text-sm text-slate-200">
            Ask your GM to add you to their campaign in Fireball.quest. Once they do,
            this page will show your sessions automatically.
          </CardDescription>
        </CardHeader>

        <CardContent class="space-y-4">
          <div class="space-y-2">
            <p class="text-xs font-semibold uppercase tracking-wide text-slate-300">
              Share this username with your GM
            </p>

            <div class="flex items-center justify-between rounded-md border border-slate-600 bg-slate-900 px-3 py-2">
              <span class="font-mono text-sm text-slate-50">
                {$username ?? "your-username"}
              </span>
            </div>

            <p class="text-[11px] text-slate-300">
              Your GM can use this username in the campaign settings to add you as a player.
            </p>
          </div>
        </CardContent>

        <CardFooter>
          <p class="text-xs text-slate-400">
            Already added to a campaign? Refresh this page after your GM saves the change.
          </p>
        </CardFooter>
      </Card>
    </div>
  {/if}
</div>
