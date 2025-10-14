<script lang="ts">
	import { onDestroy } from 'svelte';
	import { deepResearch, settings } from '$lib/stores';
	import { cancelDeepResearch } from '$lib/apis';
	import { toast } from 'svelte-sonner';
	import Spinner from '$lib/components/common/Spinner.svelte';

	export let token: string;

	let eventSource: EventSource | null = null;
	let activeRunId: string | null = null;
	let logContainer: HTMLDivElement | null = null;

	const closePanel = () => {
		deepResearch.update((state) => ({ ...state, showPanel: false }));
	};

	const cleanupStream = () => {
		if (eventSource) {
			eventSource.close();
			eventSource = null;
		}
	};

	const appendLog = (text: string) => {
		if (!text) return;
		deepResearch.update((state) => ({
			...state,
			isStreaming: true,
			log: state.log ? `${state.log}\n${text}` : text
		}));
	};

	const formatEventData = (data: string): string => {
		try {
			const parsed = JSON.parse(data);
			if (typeof parsed === 'string') {
				return parsed;
			}

			const message =
				parsed?.data?.message ??
				parsed?.data?.text ??
				parsed?.data?.output ??
				parsed?.message ??
				parsed?.text ??
				parsed?.output;

			if (message) {
				return typeof message === 'string' ? message : JSON.stringify(message, null, 2);
			}

			return JSON.stringify(parsed, null, 2);
		} catch (error) {
			return data;
		}
	};

	const startStream = (runId: string) => {
		cleanupStream();
		if (typeof window === 'undefined') return;

		const url = `${window.location.origin}/api/v1/deep-research/${runId}/stream`;
		eventSource = new EventSource(url, {
			withCredentials: true
		});

		eventSource.onmessage = (event) => {
			if (event.data === '[DONE]') {
				deepResearch.update((state) => ({ ...state, isStreaming: false }));
				cleanupStream();
				activeRunId = null;
				return;
			}

			const formatted = formatEventData(event.data);
			appendLog(formatted);
		};

		eventSource.onerror = () => {
			toast.error('Deep research stream disconnected');
			deepResearch.update((state) => ({
				...state,
				isStreaming: false
			}));
			cleanupStream();
			activeRunId = null;
		};
	};

	const stopRun = async () => {
		const { runId } = $deepResearch;
		if (!runId) return;

		cleanupStream();
		activeRunId = null;
		deepResearch.update((state) => ({ ...state, isStreaming: false, runId: null }));
		try {
			await cancelDeepResearch(token, runId);
			toast.success('Deep research run cancelled');
		} catch (error) {
			console.error(error);
			toast.error('Failed to cancel deep research run');
		}
	};

	onDestroy(() => {
		cleanupStream();
		deepResearch.update((state) => ({ ...state, isStreaming: false }));
	});

	$: {
		const { showPanel, runId } = $deepResearch;
		if (showPanel && runId) {
			if (activeRunId !== runId) {
				activeRunId = runId;
				startStream(runId);
			}
		} else {
			activeRunId = null;
			cleanupStream();
		}
	}

	$: if (logContainer) {
		logContainer.scrollTop = logContainer.scrollHeight;
	}
</script>

<div class="flex flex-col h-full">
	<header class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
		<div class="flex flex-col">
			<h2 class="text-base font-semibold">Deep Research</h2>
			<p class="text-xs text-gray-500">{ $deepResearch.runId ? `Run ID: ${$deepResearch.runId}` : 'Not started' }</p>
		</div>

		<div class="flex items-center gap-2">
			{#if $deepResearch.isStreaming}
				<button class="text-sm text-red-500" on:click={stopRun}>Stop</button>
			{/if}
			<button class="text-sm" on:click={closePanel}>Close</button>
		</div>
	</header>

	<section class="flex-1 overflow-auto p-4" bind:this={logContainer}>
		{#if $deepResearch.isStreaming}
			<div class="flex items-center gap-2 text-sm text-gray-500">
				<Spinner className="size-4" />
				<span>Streaming updates…</span>
			</div>
		{/if}

		{#if $deepResearch.log}
			<pre class="text-xs whitespace-pre-wrap leading-relaxed">{$deepResearch.log}</pre>
		{:else}
			<p class="text-xs text-gray-500">Waiting for updates…</p>
		{/if}
	</section>

	<footer class="p-4 text-xs text-gray-500 border-t border-gray-200 dark:border-gray-800">
		{$settings?.deepResearch?.hint ?? 'Deep research provides iterative updates from the orchestrator.'}
	</footer>
</div>

<style>
	:global(pre) {
		background: transparent;
	}
</style>

