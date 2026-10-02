<!-- Copyright 2026 Aayush Chawla -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<script lang="ts">
	import { health } from '$lib/stores/health';
	import { showVectorStoreSetupBanner, vectorStoreState } from '$lib/utils/vectorStore';

	let dismissed = $state(false);
</script>

{#if showVectorStoreSetupBanner($health)}
	<div class="flex items-center justify-center gap-2 bg-surface-800/60 border-b border-surface-700 px-4 py-1.5">
		<svg class="h-3.5 w-3.5 shrink-0 animate-spin text-surface-400" fill="none" viewBox="0 0 24 24" aria-hidden="true">
			<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
			<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"></path>
		</svg>
		<span class="text-xs text-surface-300">Setting up semantic search — chat and search may be slow to respond until this finishes</span>
	</div>
{:else if vectorStoreState($health) === 'unavailable' && !dismissed}
	<div class="flex items-center justify-center gap-2 bg-laya-gold/10 border-b border-laya-gold/25 px-4 py-1.5">
		<span class="text-xs text-laya-amber">Semantic search is unavailable — the vector store failed to start</span>
		<a href="/status" class="ml-1 text-xs font-medium text-laya-amber underline underline-offset-2">Status</a>
		<button
			onclick={() => (dismissed = true)}
			class="ml-2 text-surface-500 hover:text-surface-300 text-xs transition-colors"
			title="Dismiss">&times;</button
		>
	</div>
{/if}
