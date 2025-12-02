<script lang="ts">
    import { PUBLIC_BACKEND_BASE } from '$env/static/public';
    import { goto } from '$app/navigation';
    import { Button } from "$lib/components/ui/button/index.js";
    import { Label } from "$lib/components/ui/label/index.js";
    import { Input } from "$lib/components/ui/input/index.js";
    import * as Card from "$lib/components/ui/card/index.js";

    let email = $state("");
    let username = $state("");
    let displayName = $state("");
    let password = $state("");

    let submitting = $state(false);
    let failed = $state(false);
    let errorMessage = $state("");

    async function handleSignup(e: Event) {
        e.preventDefault();
        if (submitting) return;

        failed = false;
        errorMessage = "";
        submitting = true;

        try {
            const res = await fetch(PUBLIC_BACKEND_BASE + '/signup', {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    email,
                    username,
                    display_name: displayName || username,
                    password,
                }),
            });

            if (!res.ok) {
                failed = true;
                errorMessage = "Something went wrong. Please try again.";
                return;
            }

            const body = await res.json();

            if (body.status === "success") {
                // After sign up, send user to login
                goto('/login');
            } else if (body.status === "user_taken") {
                failed = true;
                errorMessage = "That email or username is already taken.";
            } else {
                failed = true;
                errorMessage = "Unexpected error. Please try again.";
            }
        } catch (err) {
            console.error(err);
            failed = true;
            errorMessage = "Network error. Please check your connection.";
        } finally {
            submitting = false;
        }
    }
</script>

<div class="flex h-full flex-1 items-center justify-center bg-slate-950">
    <Card.Root class="w-full max-w-sm bg-slate-900 text-slate-100 border-slate-800">
    <Card.Header class="space-y-3">
        <Card.Title class="text-slate-50 text-2xl">
            Create your account
        </Card.Title>

        <Card.Description class="text-slate-400">
            Enter your details below to get started.
        </Card.Description>

        <p class="text-sm text-slate-400">
            Already have an account?
            <a
                href="/login"
                class="ml-1 underline underline-offset-4 hover:text-slate-100"
            >
                Log in
            </a>
        </p>
    </Card.Header>


        <Card.Content>
            <form onsubmit={handleSignup} class="space-y-4">
                <div class="grid gap-2">
                    <Label for="email">Email</Label>
                    <Input
                        id="email"
                        type="email"
                        placeholder="you@example.com"
                        bind:value={email}
                        required
                        class="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
                    />
                </div>

                <div class="grid gap-2">
                    <Label for="username">Username</Label>
                    <Input
                        id="username"
                        type="text"
                        placeholder="Choose a username"
                        bind:value={username}
                        required
                        class="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
                    />
                </div>

                <div class="grid gap-2">
                    <Label for="displayName">Display name (optional)</Label>
                    <Input
                        id="displayName"
                        type="text"
                        placeholder="What should we call you?"
                        bind:value={displayName}
                        class="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
                    />
                    <p class="text-xs text-slate-500">
                        If left empty, we&#39;ll use your username.
                    </p>
                </div>

                <div class="grid gap-2">
                    <Label for="password">Password</Label>
                    <Input
                        id="password"
                        type="password"
                        placeholder="Create a password"
                        bind:value={password}
                        required
                        class="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
                        onkeydown={(e) => {
                            if (e.key === 'Enter') handleSignup(e);
                        }}
                    />
                </div>
            </form>
        </Card.Content>

        <Card.Footer class="flex-col gap-2">
            <Button
                type="submit"
                class="w-full bg-sky-600 hover:bg-sky-500 text-slate-50"
                onclick={handleSignup}
                disabled={submitting}
            >
                {#if submitting}
                    Signing up…
                {:else}
                    Sign Up
                {/if}
            </Button>

            {#if failed}
                <p class="text-sm text-red-400">
                    {errorMessage}
                </p>
            {/if}
        </Card.Footer>
    </Card.Root>
</div>
