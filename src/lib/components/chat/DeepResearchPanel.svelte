<script lang="ts">
import {
	deepResearchState,
	showDeepResearch,
	type DeepResearchEvent,
	type DeepResearchSource
} from '$lib/stores';
	import {
		startDeepResearchStream,
		stopDeepResearchStream,
		resetDeepResearchState
	} from '$lib/services/deepresearch';

	const extractProgress = (event: DeepResearchEvent): number | null => {
		const value = event.meta?.progress;
		return typeof value === 'number' ? value : null;
	};

const hasValidSource = (source: DeepResearchSource) =>
	typeof source.url === 'string' && source.url.length > 0;

const shouldDisplayText = (event: DeepResearchEvent): boolean => {
	const stage = (event.stage ?? '').toUpperCase();
	return Boolean(event.text) && stage !== 'DONE' && stage !== 'END';
};

const handleRetry = async () => {
	const query = $deepResearchState.query?.trim();
	if (!query) {
		return;
		}

		try {
			startDeepResearchStream(query);
			showDeepResearch.set(true);
		} catch (error) {
			console.error('Failed to restart DeepResearch stream', error);
		}
	};
</script>

<div class="flex h-full flex-col gap-4 text-sm text-gray-700 dark:text-gray-200">
	<header class="space-y-1 border-b border-gray-200 pb-3 dark:border-gray-800">
		<div class="flex items-center justify-between">
			<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Deep Research Monitor</h2>

			<div class="flex items-center gap-2">
				<button
					class="rounded-md border border-gray-300 px-2 py-1 text-xs font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
					on:click={() => {
						resetDeepResearchState();
					}}
				>
					Clear
				</button>
				<button
					class="rounded-md border border-gray-300 px-2 py-1 text-xs font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
					on:click={() => stopDeepResearchStream()}
					disabled={!$deepResearchState.isStreaming}
				>
					Stop
				</button>
				<button
					class="rounded-md bg-blue-600 px-2 py-1 text-xs font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-400"
					on:click={handleRetry}
					disabled={!$deepResearchState.query}
				>
					Restart
				</button>
			</div>
		</div>
		{#if $deepResearchState.query}
			<p class="text-xs text-gray-500 dark:text-gray-400">
				Query: <span class="break-all font-medium text-gray-800 dark:text-gray-200">
					{$deepResearchState.query}
				</span>
			</p>
		{:else}
			<p class="text-xs text-gray-500 dark:text-gray-400">
				Enter a question and press Deep Research to begin streaming updates.
			</p>
		{/if}
	</header>

	<section class="space-y-3">
		<div class="flex flex-wrap items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
			<span>Status: {$deepResearchState.isStreaming ? 'Streaming' : 'Idle'}</span>
			<span>Stage: {$deepResearchState.currentStage ?? '—'}</span>
			{#if $deepResearchState.runId}
				<span class="truncate">ID: {$deepResearchState.runId}</span>
			{/if}
			{#if $deepResearchState.lastMessageAt}
				<span>
					Updated at {new Date($deepResearchState.lastMessageAt).toLocaleTimeString()}
				</span>
			{/if}
		</div>

		{#if $deepResearchState.error}
			<div class="rounded-md border border-red-200 bg-red-50 p-3 text-xs text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300">
				{$deepResearchState.error}
			</div>
		{/if}

		<div class="space-y-2">
			<h3 class="text-sm font-semibold text-gray-900 dark:text-white">Timeline</h3>

			{#if $deepResearchState.events.length === 0}
				<p class="rounded-md border border-dashed border-gray-200 bg-gray-50 p-3 text-xs text-gray-500 dark:border-gray-700 dark:bg-gray-900/40 dark:text-gray-400">
					No events yet. Start a run to see stage-by-stage updates.
				</p>
			{:else}
				<ul class="space-y-2">
					{#each $deepResearchState.events as event}
						<li class="rounded-md border border-gray-200 bg-white p-3 shadow-sm dark:border-gray-800 dark:bg-gray-900/60">
							<div class="flex flex-wrap items-center justify-between gap-2">
								<div class="flex items-center gap-2">
									<span class="rounded bg-blue-100 px-2 py-0.5 text-[0.65rem] font-semibold uppercase tracking-wide text-blue-700 dark:bg-blue-900/40 dark:text-blue-200">
										{event.stage ?? 'EVENT'}
									</span>
									{#if event.done}
										<span class="rounded bg-emerald-100 px-2 py-0.5 text-[0.65rem] font-semibold uppercase tracking-wide text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200">
											DONE
										</span>
									{/if}
								</div>
								{#if extractProgress(event) !== null}
									<span class="text-[0.65rem] text-gray-500 dark:text-gray-400">
										Progress: {extractProgress(event)}%
									</span>
								{/if}
							</div>
							{#if shouldDisplayText(event)}
								<p class="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-gray-800 dark:text-gray-200">
									{event.text}
								</p>
							{:else if event.done}
								<p class="mt-2 text-sm italic text-gray-500 dark:text-gray-400">
									No additional summary for this stage.
								</p>
							{:else}
								<p class="mt-2 text-sm italic text-gray-500 dark:text-gray-400">
									Awaiting details from this stage…
								</p>
							{/if}
						</li>
					{/each}
				</ul>
			{/if}
		</div>
	</section>

	{#if $deepResearchState.sources.length}
		<section class="space-y-2">
			<h3 class="text-sm font-semibold text-gray-900 dark:text-white">Sources</h3>
			<ul class="space-y-2 text-xs">
				{#each $deepResearchState.sources as source}
					<li>
						{#if hasValidSource(source)}
							<a
								href={source.url ?? ''}
								target="_blank"
								rel="noreferrer"
								class="text-blue-600 hover:underline dark:text-blue-300"
							>
								{source.title ?? source.url}
							</a>
						{:else}
							<span class="text-gray-600 dark:text-gray-300">
								{source.title ?? 'Untitled source'}
							</span>
						{/if}
					</li>
				{/each}
			</ul>
		</section>
	{/if}
</div>
