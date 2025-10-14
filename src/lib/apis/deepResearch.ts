import { WEBUI_API_BASE_URL } from '$lib/constants';

type StartDeepResearchPayload = {
	inputs: Record<string, unknown>;
	params?: Record<string, unknown>;
	workflow_id?: string;
};

export type DeepResearchRun = {
	run_id: string;
	status: string;
};

const authHeader = (token: string) => ({
	Authorization: `Bearer ${token}`
});

export const startDeepResearch = async (
	token: string,
	body: StartDeepResearchPayload
): Promise<DeepResearchRun> => {
	let error: unknown = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/deep-research/start`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			...authHeader(token)
		},
		body: JSON.stringify(body)
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res as DeepResearchRun;
};

export const getDeepResearchStatus = async (
	token: string,
	runId: string
): Promise<Record<string, unknown>> => {
	let error: unknown = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/deep-research/${runId}/status`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			...authHeader(token)
		}
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res as Record<string, unknown>;
};

export const cancelDeepResearch = async (token: string, runId: string) => {
	let error: unknown = null;
	const res = await fetch(`${WEBUI_API_BASE_URL}/deep-research/${runId}/cancel`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			...authHeader(token)
		}
	})
		.then(async (r) => {
			if (!r.ok) throw await r.json();
			return r.json();
		})
		.catch((err) => {
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

