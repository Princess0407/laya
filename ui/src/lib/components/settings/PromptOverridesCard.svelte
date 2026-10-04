<!-- Copyright 2026 Aayush Chawla -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<script lang="ts">
	import { engineApi } from '$lib/api/engine';
	import { glassTheme } from '$lib/stores/glassTheme';
	import { onMount } from 'svelte';

	// Files from ~/.laya/prompts/ the engine currently uses in place of its
	// built-in prompts. null until the first status fetch completes.
	let overriddenFiles = $state<string[] | null>(null);
	let reloading = $state(false);
	let reloaded = $state(false);
	let error = $state<string | null>(null);

	async function loadStatus() {
		const { prompts } = await engineApi.getPrompts();
		overriddenFiles = prompts.filter((p) => p.overridden).map((p) => p.file);
	}

	async function reload() {
		reloading = true;
		reloaded = false;
		error = null;
		try {
			await engineApi.reloadPrompts();
			await loadStatus();
			reloaded = true;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to reload prompts';
		} finally {
			reloading = false;
		}
	}

	onMount(() => {
		loadStatus().catch((e) => {
			error = e instanceof Error ? e.message : 'Failed to load prompt status';
		});
	});
</script>

<div class="{$glassTheme ? 'glass-section' : 'rounded-lg border border-surface-700 bg-surface-800'} p-5">
	<div class="mb-1 flex items-center justify-between">
		<h3 class="text-laya-heading font-medium">Custom Prompts</h3>
		{#if reloading}
			<span class="text-laya-micro text-laya-orange">Reloading…</span>
		{:else if reloaded}
			<span class="text-laya-micro text-green-400">Reloaded</span>
		{/if}
	</div>
	<p class="mb-4 text-laya-base text-surface-400">
		Prompt files in <span class="text-surface-300">~/.laya/prompts/</span> replace the built-in
		prompt for their pipeline stage. Reload after adding, editing, or deleting a file to apply the
		change without restarting.
	</p>

	<button
		onclick={reload}
		disabled={reloading}
		class="rounded-md border border-surface-600 px-3 py-1.5 text-laya-secondary text-surface-200 transition-colors hover:border-laya-orange hover:text-laya-orange disabled:cursor-not-allowed disabled:opacity-50"
	>
		Reload prompts
	</button>

	{#if error}
		<p class="mt-2 text-laya-secondary text-red-400">{error}</p>
	{/if}

	{#if overriddenFiles !== null}
		<p class="mt-3 text-laya-secondary text-surface-500">
			{#if overriddenFiles.length === 0}
				No custom prompts in use.
			{:else}
				In use:
				<span class="text-surface-300">{overriddenFiles.join(', ')}</span>
			{/if}
		</p>
	{/if}
</div>
