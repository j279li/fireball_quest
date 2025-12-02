import { writable } from "svelte/store";

export const scrub = {
    username: writable<string | null>(null)
}

export const username = writable<string | null>(null);
