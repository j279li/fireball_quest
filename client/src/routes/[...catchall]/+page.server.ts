import { redirect } from '@sveltejs/kit';

// Redirect unknown paths to /home to avoid SvelteKit trying to render
// a missing +page.svelte for the catchall route (useful for dev).
export function load() {
	throw redirect(307, '/home');
}
