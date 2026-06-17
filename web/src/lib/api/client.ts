import type {
	KeyOut,
	KeyCreated,
	KeyUpdate,
	BulkKeyToggle,
	BulkActionResult,
	RouterSettings,
	ChatCompletionRequest,
	ChatCompletionResponse,
	ClassifyRequest,
	ClassifyResponse
} from '$lib/types';

const BASE = '';

class ApiError extends Error {
	constructor(
		public status: number,
		message: string
	) {
		super(message);
		this.name = 'ApiError';
	}
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(`${BASE}${path}`, {
		...init,
		headers: {
			'Content-Type': 'application/json',
			...init?.headers
		}
	});
	if (!res.ok) {
		const body = await res.text();
		throw new ApiError(res.status, body);
	}
	return res.json() as Promise<T>;
}

// ── Keys ─────────────────────────────────────────────────────────────────

export const keys = {
	list: () => request<KeyOut[]>('/api/v1/keys'),

	create: (name: string) =>
		request<KeyCreated>('/api/v1/keys', {
			method: 'POST',
			body: JSON.stringify({ name })
		}),

	update: (id: string, patch: KeyUpdate) =>
		request<KeyOut>(`/api/v1/keys/${id}`, {
			method: 'PATCH',
			body: JSON.stringify(patch)
		}),

	renew: (id: string) =>
		request<KeyCreated>(`/api/v1/keys/${id}/renew`, { method: 'POST' }),

	delete: (id: string) =>
		fetch(`${BASE}/api/v1/keys/${id}`, { method: 'DELETE' }).then((r) => {
			if (!r.ok) throw new ApiError(r.status, r.statusText);
		}),

	bulkToggle: (ids: string[], is_active: boolean) =>
		request<BulkActionResult>('/api/v1/keys/bulk-toggle', {
			method: 'POST',
			body: JSON.stringify({ ids, is_active } satisfies BulkKeyToggle)
		}),

	bulkDelete: (ids: string[]) =>
		request<BulkActionResult>('/api/v1/keys/bulk-delete', {
			method: 'POST',
			body: JSON.stringify({ ids })
		})
};

// ── Settings ─────────────────────────────────────────────────────────────

export const settings = {
	get: () => request<RouterSettings>('/api/settings'),

	save: (s: RouterSettings) =>
		request<{ status: string }>('/api/settings', {
			method: 'POST',
			body: JSON.stringify(s)
		})
};

// ── Chat / Classify ──────────────────────────────────────────────────────

export const chat = {
	completions: (req: ChatCompletionRequest, apiKey?: string) =>
		request<ChatCompletionResponse>('/v1/chat/completions', {
			method: 'POST',
			headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {},
			body: JSON.stringify(req)
		}),

	classify: (req: ClassifyRequest, apiKey?: string) =>
		request<ClassifyResponse>('/api/v1/classify', {
			method: 'POST',
			headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {},
			body: JSON.stringify(req)
		})
};
