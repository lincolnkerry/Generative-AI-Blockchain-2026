/** API response types matching Pydantic models in server/api/routes/keys.py */

export interface KeyOut {
	id: string;
	name: string;
	prefix: string;
	is_active: boolean;
	last_used_at: string | null;
	created_at: string;
}

export interface KeyCreated {
	id: string;
	name: string;
	api_key: string;
	message: string;
}

export interface KeyUpdate {
	name?: string;
	is_active?: boolean;
}

export interface BulkKeyToggle {
	ids: string[];
	is_active: boolean;
}

export interface BulkActionResult {
	updated: number;
	ids: string[];
	errors: string[];
}

export interface ModelOut {
	id: string;
	model_id: string;
	display_name: string | null;
	location: string;
	tier: string;
	cost_per_1m_tokens: number;
	is_active: boolean;
	created_at: string;
}

export interface AgentConfig {
	model: string;
	temperature?: number;
	max_tokens?: number;
}

export interface RouterSettings {
	extractor: AgentConfig;
	judge?: AgentConfig;
	router?: AgentConfig;
	generator?: AgentConfig;
	models?: ModelOut[];
}

export interface ChatMessage {
	role: 'user' | 'assistant' | 'system';
	content: string;
}

export interface ChatCompletionRequest {
	model: string;
	messages: ChatMessage[];
}

export interface PipelineRecord {
	category: string;
	span: string;
	confidence: number;
	is_essential?: boolean;
	reasoning?: string;
}

export interface PrivacyRouterMeta {
	is_sensitive: boolean;
	records: PipelineRecord[];
	policy_action: string;
	route: { endpoint: string; requires_masking: boolean };
}

export interface ChatCompletionResponse {
	id: string;
	object: string;
	created: number;
	model: string;
	choices: {
		index: number;
		message: ChatMessage;
		finish_reason: string;
	}[];
	usage: {
		prompt_tokens: number;
		completion_tokens: number;
		total_tokens: number;
	};
	privacy_router?: PrivacyRouterMeta;
}

export interface ClassifyRequest {
	text: string;
}

export interface ClassifyResponse {
	is_sensitive: boolean;
	records: PipelineRecord[];
	policy_action: string;
	route: {
		endpoint: string;
		requires_masking: boolean;
		description: string;
	};
	decision?: string;
}
