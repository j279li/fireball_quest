<script lang="ts">
    import { PUBLIC_BACKEND_BASE } from '$env/static/public';
    import { goto } from '$app/navigation';
    import { Button } from "$lib/components/ui/button/index.js";
    import { Label } from "$lib/components/ui/label/index.js";
    import { Input } from "$lib/components/ui/input/index.js";
    import * as Card from "$lib/components/ui/card/index.js";
    import { username } from '$lib/test.ts';

    let failed = $state(false);
    let usr = $state("");
    let password = $state("");

    async function handleLogin(e: Event) {
        e.preventDefault();
        failed = false;

        const formData = new FormData();
        formData.append('username', usr);
        formData.append('password', password);

        const res = await fetch(PUBLIC_BACKEND_BASE + '/token', {
            method: "POST",
            body: formData,
        });

        if (res.ok) {
            const { access_token } = await res.json();
            localStorage.setItem('token', access_token);
            console.log('sss', usr);
            $username = usr;
            goto('/home');
        } else failed = true;
    }
</script>

<div class="flex h-full flex-1 items-center justify-center bg-slate-950">
    <Card.Root class="w-full max-w-sm bg-slate-900 text-slate-100 border border-slate-800">
        <Card.Header class="space-y-3">
            <Card.Title class="text-slate-50 text-2xl">
                Login to your account
            </Card.Title>

            <Card.Description class="text-slate-400">
                Enter your username below to login to your account.
            </Card.Description>

            <p class="text-sm text-slate-400">
                Don&apos;t have an account?
                <a
                    href="/signup"
                    class="ml-1 underline underline-offset-4 hover:text-slate-100"
                >
                    Sign up
                </a>
            </p>
        </Card.Header>

        <Card.Content>
            <form onsubmit={handleLogin} class="space-y-4">
                <div class="grid gap-2">
                    <Label for="username">Username</Label>
                    <Input
                        id="username"
                        type="text"
                        placeholder="Enter username"
                        bind:value={usr}
                        required
                        autofocus
                        class="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
                    />
                </div>

                <div class="grid gap-2">
                    <div class="flex items-center">
                        <Label for="password">Password</Label>
                        <a
                            href="/forgot-password"
                            class="ml-auto inline-block text-sm underline-offset-4 hover:underline text-slate-400 hover:text-slate-100"
                        >
                            Forgot your password?
                        </a>
                    </div>
                    <Input
                        id="password"
                        type="password"
                        placeholder="Enter password"
                        bind:value={password}
                        required
                        class="bg-slate-900 border-slate-700 text-slate-100 placeholder:text-slate-500"
                        onkeydown={(e) => {
                            if (e.key === 'Enter') handleLogin(e);
                        }}
                    />
                </div>
            </form>
        </Card.Content>

        <Card.Footer class="flex-col gap-2">
            <Button
                type="submit"
                class="w-full bg-sky-600 hover:bg-sky-500 text-slate-50"
                onclick={handleLogin}
            >
                Login
            </Button>

            {#if failed}
                <p class="text-sm text-red-400">Login failed. Please try again.</p>
            {/if}
        </Card.Footer>
    </Card.Root>
</div>
