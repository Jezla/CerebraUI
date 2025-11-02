import { deepResearchState, createDeepResearchInitialState } from '$lib/stores';
import type { DeepResearchEvent, DeepResearchState, DeepResearchSource } from '$lib/stores';

const SSE_ENDPOINT = '/ai/deepresearch/stream';

let eventSource: EventSource | null = null;
let abortCleanup: (() => void) | null = null;

type MergeableSources = DeepResearchSource[] | undefined;

export type StartDeepResearchOptions = {
	withCredentials?: boolean;
	signal?: AbortSignal;
	onEvent?: (message: DeepResearchEvent) => void;
	onError?: (message: string) => void;
};

export type StopDeepResearchOptions = {
	reset?: boolean;
	error?: string | null;
};

export function resetDeepResearchState() {
	deepResearchState.set(createDeepResearchInitialState());
}

export function stopDeepResearchStream(options: StopDeepResearchOptions = {}) {
	closeEventSource();

	const { reset = false, error = null } = options;

	deepResearchState.update((state) => {
		if (reset) {
			return createDeepResearchInitialState();
		}

		return {
			...state,
			isStreaming: false,
			error: error ?? state.error
		};
	});
}

export function startDeepResearchStream(query: string, options: StartDeepResearchOptions = {}) {
	if (typeof window === 'undefined') {
		console.warn('startDeepResearchStream should only be called in the browser.');
		return;
	}

	if (!query?.trim()) {
		throw new Error('DeepResearch query cannot be empty.');
	}

	const normalizedQuery = query.trim();
	const { withCredentials = true, signal, onEvent, onError } = options;

	// Ensure any previous stream is stopped before starting a new one.
	stopDeepResearchStream({ reset: true });

	const freshState = createDeepResearchInitialState();
	freshState.isStreaming = true;
	freshState.query = normalizedQuery;

	deepResearchState.set(freshState);

	const url = `${SSE_ENDPOINT}?q=${encodeURIComponent(normalizedQuery)}`;
	const source = new EventSource(url, { withCredentials });

	eventSource = source;

	attachAbortHandler(signal);

	source.onmessage = (event: MessageEvent<string>) => {
		const payload = parseEventData(event.data);
		if (!payload) return;

		deepResearchState.update((state) => applyMessageToState(state, payload));

		onEvent?.(payload);

		if (payload.done) {
			stopDeepResearchStream();
		}
	};

	source.onerror = () => {
		const message = 'DeepResearch stream interrupted.';
		stopDeepResearchStream({ error: message });
		onError?.(message);
	};
}

function closeEventSource() {
	if (abortCleanup) {
		abortCleanup();
		abortCleanup = null;
	}

	if (eventSource) {
		eventSource.close();
		eventSource = null;
	}
}

function attachAbortHandler(signal: AbortSignal | undefined) {
	if (!signal) return;

	const abortHandler = () => {
		stopDeepResearchStream();
	};

	signal.addEventListener('abort', abortHandler, { once: true });
	abortCleanup = () => signal.removeEventListener('abort', abortHandler);

	if (signal.aborted) {
		abortHandler();
	}
}

function parseEventData(data: string): DeepResearchEvent | null {
	if (!data) return null;

	try {
		const parsed = JSON.parse(data);
		if (parsed && typeof parsed === 'object') {
			return parsed as DeepResearchEvent;
		}
	} catch (error) {
		console.warn('Unable to parse DeepResearch event payload.', error);
	}

	return null;
}

function applyMessageToState(state: DeepResearchState, message: DeepResearchEvent): DeepResearchState {
	const nextEvents = [...state.events];

	if (!message.done && nextEvents.length > 0) {
		const lastIdx = nextEvents.length - 1;
		const lastEvent = nextEvents[lastIdx];
		if (lastEvent?.stage === message.stage) {
			const merged: DeepResearchEvent = { ...lastEvent };

			const previousText = typeof lastEvent.text === 'string' ? lastEvent.text : '';
			const incomingText = typeof message.text === 'string' ? message.text : '';

			if (incomingText) {
				merged.text = previousText
					? `${previousText}\n${incomingText}`.trim()
					: incomingText;
			}

			if (message.meta) {
				merged.meta = {
					...(lastEvent.meta ?? {}),
					...message.meta
				};
			}

			if (message.done) {
				merged.done = true;
			}

			nextEvents[lastIdx] = merged;
		} else {
			nextEvents.push(message);
		}
	} else {
		nextEvents.push(message);
	}
	const nextSources = mergeSources(state.sources, message.meta?.sources);
	const runId =
		typeof message.meta === 'object' && message.meta !== null && typeof message.meta.run_id === 'string'
			? message.meta.run_id
			: state.runId;
	const nextError =
		message.stage === 'ERROR' ? (message.text ?? state.error ?? 'DeepResearch stream reported an error.') : state.error;

	return {
		...state,
		events: nextEvents,
		currentStage: message.stage ?? state.currentStage,
		sources: nextSources,
		runId,
		error: nextError,
		lastMessageAt: Date.now(),
		isStreaming: message.done ? false : state.isStreaming
	};
}

function mergeSources(existing: DeepResearchSource[], incoming: MergeableSources): DeepResearchSource[] {
	if (!Array.isArray(incoming) || incoming.length === 0) {
		return existing;
	}

	const next: DeepResearchSource[] = [...existing];

	for (const candidate of incoming) {
		if (!candidate || typeof candidate !== 'object') continue;

		const normalized = candidate as DeepResearchSource;
		if (!next.some((source) => (source.url ?? source.title) === (normalized.url ?? normalized.title))) {
			next.push({ ...normalized });
		}
	}

	return next;
}
