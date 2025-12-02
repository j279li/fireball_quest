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
    Play,
    X,
    AlertCircle,
    CheckCircle2 as CheckIcon
  } from "lucide-svelte";

  type Campaign = {
    id: number;
    name: string;
    description?: string;
    game_system_id?: number;
    created_at?: string;
    is_owner?: boolean;
  };

  let loading = true;
  let ownedCampaigns: Campaign[] = [];
  let allCampaigns: Campaign[] = [];
  let isGM = false;
  let currentCampaignId: number | null = null;

  // Campaign selector modal
  let campaignSelectorOpen = false;
  let showCreateCampaignForm = false;
  let newCampaignName = "";
  let newCampaignDescription = "";
  let createCampaignLoading = false;
  let createCampaignError = "";




  // Simple local toast
  let showToast = false;
  let toastMessage = "";

  // Campaign management functions
  async function loadAllCampaigns(token: string) {
    try {
      const res = await fetch(`${PUBLIC_BACKEND_BASE}/campaigns`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        const campaigns = await res.json();
        allCampaigns = Array.isArray(campaigns) ? campaigns : [];
        
        // If user has campaigns, select the first one
        if (allCampaigns.length > 0 && !currentCampaignId) {
          currentCampaignId = allCampaigns[0].id;
        }
      } else {
        allCampaigns = [];
      }
    } catch (err) {
      console.error("Failed to load campaigns:", err);
      allCampaigns = [];
    }
  }

  function openCampaignSelector() {
    campaignSelectorOpen = true;
    showCreateCampaignForm = false;
    newCampaignName = "";
    newCampaignDescription = "";
    createCampaignError = "";
  }

  function closeCampaignSelector() {
    if (createCampaignLoading) return;
    campaignSelectorOpen = false;
    showCreateCampaignForm = false;
  }

  async function selectCampaign(campaignId: number) {
    currentCampaignId = campaignId;
    const token = localStorage.getItem("token");
    // selection only; members/invite moved into chat view
    closeCampaignSelector();
  }

  async function createCampaign() {
    createCampaignError = "";

    if (!newCampaignName.trim()) {
      createCampaignError = "Please enter a campaign name.";
      return;
    }

    const token = localStorage.getItem("token");
    if (!token) {
      createCampaignError = "You must be logged in.";
      return;
    }

    createCampaignLoading = true;
    try {
      const res = await fetch(`${PUBLIC_BACKEND_BASE}/campaigns`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          name: newCampaignName.trim(),
          description: newCampaignDescription.trim(),
          game_system_id: 1
        })
      });

      if (res.ok) {
        const data = await res.json();
        await loadAllCampaigns(token);
        // sessions are currently not used; open chat per-campaign instead
        
        // Select the newly created campaign
        if (data.campaign_id) {
          await selectCampaign(data.campaign_id);
        }

        toastMessage = `Campaign "${newCampaignName.trim()}" created!`;
        showToast = true;
        setTimeout(() => {
          showToast = false;
        }, 3000);

        closeCampaignSelector();
      } else {
        let msg = "Could not create campaign.";
        try {
          const data = await res.json();
          if (typeof data?.detail === "string") msg = data.detail;
        } catch {
          /* ignore */
        }
        createCampaignError = msg;
      }
    } catch (e) {
      console.error("Create campaign failed:", e);
      createCampaignError = "Something went wrong. Please try again.";
    } finally {
      createCampaignLoading = false;
    }
  }

  // no sessions: campaigns-only view

  onMount(async () => {
    const token = localStorage.getItem("token");
    if (!token) {
	goto("/login");
      loading = false;
      return;
    }

    try {
      // 1) Load all campaigns user has access to
      await loadAllCampaigns(token);

      // 2) Load owned campaigns for isGM check
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

      // 3) If user has campaigns, load members for the selected campaign
      if (allCampaigns.length > 0) {
        if (!currentCampaignId) {
          currentCampaignId = allCampaigns[0].id;
        }
        // members/invite are loaded inside the chat view now
      } else {
        // No campaigns - open selector so they can create one
        openCampaignSelector();
      }
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

      // Previously redirected non-GM users straight into chat; removed so
      // everyone stays on the campaigns list by default.
    } catch (err) {
      console.error("Error loading home data:", err);
      ownedCampaigns = [];
      isGM = false;
    } finally {
      loading = false;
    }
  });

  // Helper: no session helpers needed in campaign-only view
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
            {#if currentCampaignId}
              {allCampaigns.find(c => c.id === currentCampaignId)?.name ?? "Your RPG campaigns and sessions"}
            {:else}
              Your RPG campaigns and sessions
            {/if}
          </p>
        </div>

        <div class="flex items-center gap-3">
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-md border border-slate-600 px-3 py-2 text-sm font-medium text-slate-300 bg-transparent hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400"
            on:click={openCampaignSelector}
          >
            {allCampaigns.length > 1 ? "Select" : "Create"} Campaign
          </button>
        </div>
      </header>

      <!-- (Players list removed — invite moved into chat) -->

      <!-- Campaigns list -->
      <section class="space-y-4">
        <h2 class="text-xl font-semibold text-slate-50">Your Campaigns</h2>

        {#if allCampaigns.length === 0}
          <p class="text-sm text-slate-400">You don’t have any campaigns yet. Create one to get started.</p>
        {:else}
          <div class="grid gap-6 md:grid-cols-2">
            {#each allCampaigns as c}
              <Card class="bg-slate-800 border-slate-700 shadow-sm flex flex-col text-slate-50">
                <CardHeader class="flex flex-row items-start justify-between gap-4 pb-3">
                  <div>
                    <CardTitle class="text-lg text-slate-50">{c.name}</CardTitle>
                    <CardDescription class="text-sm text-slate-300">{c.description ?? ''}</CardDescription>
                  </div>

                  {#if c.is_owner}
                    <Badge variant="outline" class="border-emerald-400/70 text-emerald-200 bg-emerald-500/15">GM</Badge>
                  {/if}
                </CardHeader>

                <CardContent class="space-y-3 text-sm text-slate-200">
                  <p class="text-sm text-slate-300">{c.description ?? 'No description'}</p>
                </CardContent>

                <CardFooter class="mt-auto pt-2">
                  <button
                    type="button"
                    class="inline-flex w-full items-center justify-center gap-2 rounded-md bg-sky-600 px-3 py-2 text-sm font-medium text-slate-50 shadow-sm hover:bg-sky-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
                    on:click={() => goto(`/chat/${c.id}`)}
                  >
                    <Play class="w-4 h-4" />
                    <span>Open Chat</span>
                  </button>
                </CardFooter>
              </Card>
            {/each}
          </div>
        {/if}
      </section>

      <!-- Invite modal removed from home; invite belongs in chat UI -->



    </div>

  {:else if allCampaigns.length > 0}
    <!-- PLAYER VIEW - list campaigns and open chat -->
    <div class="relative max-w-6xl mx-auto w-full py-8 px-6 space-y-6">
      <header class="flex items-center justify-between gap-4">
        <div>
          <h1 class="text-3xl font-semibold tracking-tight text-slate-50">Fireball.quest</h1>
          <p class="text-sm text-slate-300">Your Campaigns</p>
        </div>
        <Button on:click={openCampaignSelector} variant="outline" class="border-sky-500/70 text-sky-300">Select Campaign</Button>
      </header>

      <div class="grid gap-6 md:grid-cols-2">
        {#each allCampaigns as c}
          <Card class="bg-slate-800 border-slate-700 hover:bg-slate-750 cursor-pointer">
            <CardHeader>
              <div class="flex-1">
                <CardTitle class="text-slate-50">{c.name}</CardTitle>
                {#if c.description}
                  <CardDescription class="text-slate-300">{c.description}</CardDescription>
                {/if}
              </div>
              {#if c.is_owner}
                <Badge variant="secondary" class="ml-2 bg-sky-600/20 text-sky-300 border-sky-500/30">GM</Badge>
              {/if}
            </CardHeader>
            <CardFooter>
              <div class="flex gap-2 w-full">
                <button class="flex-1 inline-flex items-center justify-center gap-2 rounded-md bg-sky-600 px-3 py-2 text-sm font-medium text-slate-50" on:click={() => goto(`/chat/${c.id}`)}>
                  <Play class="w-4 h-4" />
                  <span>Open Chat</span>
                </button>
                <button class="px-3 py-2 rounded-md border border-slate-600 text-slate-300" on:click={() => selectCampaign(c.id)}>
                  Select
                </button>
              </div>
            </CardFooter>
          </Card>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Campaign Selector Modal -->
  {#if campaignSelectorOpen}
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div class="w-full max-w-lg rounded-xl bg-slate-900 border border-slate-700 shadow-2xl max-h-[80vh] flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-slate-700">
          <h2 class="text-lg font-semibold text-slate-50">
            {showCreateCampaignForm ? "Create New Campaign" : "Select Campaign"}
          </h2>
          <button
            type="button"
            class="rounded-full p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-100"
            on:click={closeCampaignSelector}
            aria-label="Close"
          >
            <X class="w-4 h-4" />
          </button>
        </div>

        <!-- Body -->
        <div class="px-4 py-4 space-y-3 overflow-y-auto flex-1">
          {#if !showCreateCampaignForm}
            <!-- Campaign List -->
            {#if allCampaigns.length > 0}
              <div class="space-y-2">
                {#each allCampaigns as campaign}
                  <button
                    type="button"
                    class="w-full text-left px-4 py-3 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-750 hover:border-sky-500 transition-colors"
                    on:click={() => selectCampaign(campaign.id)}
                  >
                    <div class="flex items-start justify-between">
                      <div class="flex-1">
                        <p class="font-medium text-slate-50">{campaign.name}</p>
                        {#if campaign.description}
                          <p class="text-xs text-slate-400 mt-1">{campaign.description}</p>
                        {/if}
                      </div>
                      {#if campaign.is_owner}
                        <Badge variant="secondary" class="ml-2 bg-sky-600/20 text-sky-300 border-sky-500/30">
                          GM
                        </Badge>
                      {/if}
                    </div>
                  </button>
                {/each}
              </div>
            {/if}

            <!-- Create New Campaign Button -->
            <button
              type="button"
              class="w-full px-4 py-3 rounded-lg border-2 border-dashed border-slate-600 hover:border-sky-500 text-slate-400 hover:text-sky-300 transition-colors"
              on:click={() => showCreateCampaignForm = true}
            >
              <span class="text-sm font-medium">+ Create New Campaign</span>
            </button>
          {:else}
            <!-- Create Campaign Form -->
            <div class="space-y-4">
              <div class="space-y-1.5">
                <label class="text-xs font-medium text-slate-200">
                  Campaign Name
                </label>
                <Input
                  placeholder="e.g. Lost Mines of Phandelver"
                  bind:value={newCampaignName}
                  disabled={createCampaignLoading}
                  class="bg-slate-900 border-slate-700 text-slate-50 placeholder:text-slate-500"
                  on:keydown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      createCampaign();
                    }
                  }}
                />
              </div>

              <div class="space-y-1.5">
                <label class="text-xs font-medium text-slate-200">
                  Description <span class="text-slate-500">(optional)</span>
                </label>
                <Input
                  placeholder="A brief description of your campaign"
                  bind:value={newCampaignDescription}
                  disabled={createCampaignLoading}
                  class="bg-slate-900 border-slate-700 text-slate-50 placeholder:text-slate-500"
                />
              </div>

              {#if createCampaignError}
                <div class="flex items-center gap-2 text-xs text-red-400">
                  <AlertCircle class="w-4 h-4" />
                  <span>{createCampaignError}</span>
                </div>
              {/if}

              <div class="flex items-center gap-2 pt-2">
                <button
                  type="button"
                  class="flex-1 px-3 py-2 rounded-md border border-slate-600 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  on:click={() => showCreateCampaignForm = false}
                  disabled={createCampaignLoading}
                >
                  Back
                </button>

                <button
                  type="button"
                  class="flex-1 px-3 py-2 rounded-md bg-sky-600 hover:bg-sky-500 text-slate-50 inline-flex items-center justify-center gap-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  on:click={createCampaign}
                  disabled={createCampaignLoading}
                >
                  {#if createCampaignLoading}
                    <span class="h-3 w-3 rounded-full border-2 border-slate-200 border-t-transparent animate-spin"></span>
                    <span>Creating…</span>
                  {:else}
                    <span>Create Campaign</span>
                  {/if}
                </button>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>
