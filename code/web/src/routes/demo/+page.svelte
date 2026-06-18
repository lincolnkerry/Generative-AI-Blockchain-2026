<script lang="ts">
	import type { ChatMessage, ChatCompletionResponse, PrivacyRouterMeta } from '$lib/types';
	import { settings as settingsApi } from '$lib/api';
	import { Button, Card, Select, Input, LangToggle } from '$lib/components/ui';
	import { t } from '$lib/i18n';
	import { ChatBubble, ChatInput } from '$lib/components/chat';
	import { get } from 'svelte/store';

	interface ChatEntry {
		message: ChatMessage;
		meta: PrivacyRouterMeta | null;
	}

	let messages = $state<ChatEntry[]>([]);
	let loading = $state(false);
	let apiKey = $state('');
	let selectedModel = $state('');
	let models = $state<{ value: string; label: string }[]>([]);

	$effect(() => {
		settingsApi.get().then((s) => {
			models = (s.models ?? []).map((m) => ({
				value: m.model_id,
				label: m.display_name ?? m.model_id
			}));
			if (!selectedModel && models.length > 0) {
				selectedModel = models[0].value;
			}
		});
	});

	async function handleSend(text: string) {
		messages = [...messages, { message: { role: 'user', content: text }, meta: null }];
		loading = true;

		try {
			const chatMessages: ChatMessage[] = messages.map((m) => m.message);
			const res = await fetch('/v1/chat/completions', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {})
				},
				body: JSON.stringify({
					model: selectedModel,
					messages: chatMessages
				})
			});

			if (!res.ok) {
				const errText = await res.text();
				messages = [
					...messages,
					{ message: { role: 'assistant', content: `${get(t)('alert.error')}: ${errText}` }, meta: null }
				];
				return;
			}

			const data = (await res.json()) as ChatCompletionResponse;
			const assistantMsg = data.choices?.[0]?.message;
			if (assistantMsg) {
				messages = [
					...messages,
					{ message: assistantMsg, meta: data.privacy_router ?? null }
				];
			}
		} catch (e) {
			messages = [
				...messages,
			{ message: { role: 'assistant', content: `${get(t)('alert.network_error')}: ${e instanceof Error ? e.message : String(e)}` }, meta: null }
			];
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>{$t('demo.title')} — Privacy Router</title>
</svelte:head>

<div class="min-h-screen bg-slate-950 text-slate-200 flex flex-col">
	<!-- Header -->
	<header class="border-b border-slate-800 px-6 py-4">
		<div class="max-w-3xl mx-auto flex items-center justify-between">
			<a href="/" class="text-sm text-slate-400 hover:text-white transition">{$t('nav.back')}</a>
			<div class="flex items-center gap-3">
				<span class="text-xs text-slate-500">{$t('nav.demo')}</span>
				<LangToggle />
			</div>
		</div>
	</header>

	<!-- Settings bar -->
	<div class="border-b border-slate-800 px-6 py-3">
		<div class="max-w-3xl mx-auto flex items-end gap-4">
			<div class="flex-1">
				<Select bind:value={selectedModel} options={models} label={$t('demo.model.label')} />
			</div>
			<div class="flex-1">
				<Input bind:value={apiKey} label={$t('demo.apikey.label')} placeholder={$t('demo.apikey.placeholder')} type="password" />
			</div>
		</div>
	</div>

	<!-- Messages -->
	<main class="flex-1 overflow-y-auto px-6 py-6">
		<div class="max-w-3xl mx-auto space-y-4">
			{#if messages.length === 0}
				<div class="text-center text-slate-500 py-16">
					<p class="text-lg mb-2">💬</p>
					<p>{$t('demo.empty')}</p>
				</div>
			{/if}
			{#each messages as entry, i (i)}
				<ChatBubble message={entry.message} meta={entry.meta} />
			{/each}
			{#if loading}
				<div class="flex gap-3">
					<div class="h-8 w-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold">A</div>
					<div class="rounded-2xl bg-slate-800 px-4 py-2.5 text-sm text-slate-400">
						<span class="animate-pulse">{$t('demo.thinking')}</span>
					</div>
				</div>
			{/if}
		</div>
	</main>

	<!-- Input -->
	<div class="border-t border-slate-800 px-6 py-4">
		<div class="max-w-3xl mx-auto">
			<ChatInput onsend={handleSend} disabled={loading} />
		</div>
	</div>
</div>
