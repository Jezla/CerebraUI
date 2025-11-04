<script lang="ts">
	import { onDestroy } from 'svelte';
	import {
		startDeepResearchStream,
		stopDeepResearchStream,
		resetDeepResearchState
	} from '$lib/services/deepresearch';
	import { deepResearchState } from '$lib/stores';
	import type { DeepResearchEvent, DeepResearchSource } from '$lib/stores';

	let query = '';
	let localError: string | null = null;

	const handleStart = () => {
		localError = null;

		try {
			startDeepResearchStream(query);
		} catch (error) {
			localError =
				error instanceof Error ? error.message : 'Failed to start Deep Research stream. Please try again later.';
		}
	};

	const handleStop = () => {
		stopDeepResearchStream();
	};

	const handleReset = () => {
		localError = null;
		resetDeepResearchState();
	};

	onDestroy(() => {
		stopDeepResearchStream();
	});

	const extractProgress = (event: DeepResearchEvent): number | null => {
		const value = event.meta?.progress;
		return typeof value === 'number' ? value : null;
	};

const isValidSource = (source: DeepResearchSource) =>
	typeof source.url === 'string' && source.url.length > 0;

const shouldDisplayText = (event: DeepResearchEvent): boolean => {
	const stage = (event.stage ?? '').toUpperCase();
	return Boolean(event.text) && stage !== 'DONE' && stage !== 'END';
};
</script>

<div class="mx-auto flex max-w-4xl flex-col gap-6 p-6">
	<section class="space-y-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
		<header class="space-y-2">
			<h1 class="text-2xl font-semibold text-gray-900">Deep Research Stream Demo</h1>
			<p class="text-sm text-gray-600">
				Track stage-by-stage updates via SSE. Enter a query and click “Start” to monitor the live feed and sources.
			</p>
		</header>

		<form class="flex flex-col gap-3 sm:flex-row" on:submit|preventDefault={handleStart}>
			<input
				class="flex-1 rounded-md border border-gray-300 bg-gray-50 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
				placeholder="Ask a research question, e.g. “Why is the sky blue?”"
				bind:value={query}
				autocomplete="off"
			/>

			<div class="flex gap-2">
				<button
					type="submit"
					class="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
					disabled={$deepResearchState.isStreaming || !query.trim()}
				>
					{$deepResearchState.isStreaming ? 'Streaming…' : 'Start'}
				</button>
				<button
					type="button"
					class="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:text-gray-400"
					on:click={handleStop}
					disabled={!$deepResearchState.isStreaming}
				>
					Stop
				</button>
				<button
					type="button"
					class="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50"
					on:click={handleReset}
				>
					Clear
				</button>
			</div>
		</form>

		{#if localError}
			<p class="text-sm text-red-600">{localError}</p>
		{:else if $deepResearchState.error}
			<p class="text-sm text-red-600">{$deepResearchState.error}</p>
		{/if}
	</section>

	<section class="space-y-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
		<div class="flex flex-wrap items-center gap-4 text-sm text-gray-600">
			<div>Status: {$deepResearchState.isStreaming ? 'Streaming' : 'Idle'}</div>
			<div>Current stage: {$deepResearchState.currentStage ?? '—'}</div>
			{#if $deepResearchState.runId}
				<div class="truncate">Run ID: {$deepResearchState.runId}</div>
			{/if}
			{#if $deepResearchState.lastMessageAt}
				<div>
					Updated at: {new Date($deepResearchState.lastMessageAt).toLocaleTimeString()}
				</div>
			{/if}
		</div>

		<div class="space-y-3">
			<h2 class="text-lg font-medium text-gray-900">Stage updates</h2>
			{#if $deepResearchState.events.length === 0}
				<p class="rounded-md border border-dashed border-gray-300 bg-gray-50 p-4 text-sm text-gray-500">
					No events yet. Submit a query to start streaming.
				</p>
			{:else}
				<ul class="space-y-3">
					{#each $deepResearchState.events as event}
						<li class="space-y-2 rounded-md border border-gray-200 bg-gray-50 p-3">
							<div class="flex flex-wrap items-center justify-between gap-2">
								<div class="flex items-center gap-2">
									<span class="rounded bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700">
										{event.stage ?? 'Event'}
									</span>
									{#if event.done}
										<span class="rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
											DONE
										</span>
									{/if}
								</div>
								{#if extractProgress(event) !== null}
									<span class="text-xs text-gray-500">
										Progress: {extractProgress(event)}%
									</span>
								{/if}
							</div>
				{#if shouldDisplayText(event)}
					<p class="whitespace-pre-wrap text-sm leading-relaxed text-gray-800">
						{event.text}
					</p>
							{:else if event.done}
								<p class="text-sm italic text-gray-500">
									No additional summary for this stage.
								</p>
							{:else}
								<p class="text-sm italic text-gray-500">
									Waiting for output…
								</p>
							{/if}
						</li>
					{/each}
				</ul>
			{/if}
		</div>

		{#if $deepResearchState.sources.length}
			<div class="space-y-3">
				<h2 class="text-lg font-medium text-gray-900">Sources</h2>
				<ul class="space-y-2 text-sm">
					{#each $deepResearchState.sources as source}
						<li>
							{#if isValidSource(source)}
								<a
									href={source.url ?? ''}
									target="_blank"
									rel="noreferrer"
									class="text-blue-600 hover:underline"
								>
									{source.title ?? source.url}
								</a>
							{:else}
								<span class="text-gray-600">{source.title ?? 'Untitled source'}</span>
							{/if}
						</li>
					{/each}
				</ul>
			</div>
		{/if}
	</section>
</div>
