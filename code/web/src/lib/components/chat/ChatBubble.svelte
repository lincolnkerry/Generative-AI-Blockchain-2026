<script lang="ts">
	import type { ChatMessage, PrivacyRouterMeta } from '$lib/types';
	import { t } from '$lib/i18n';
	import { get } from 'svelte/store';

	interface Props {
		message: ChatMessage;
		meta?: PrivacyRouterMeta | null;
	}

	let { message, meta }: Props = $props();

	let isUser = $derived(message.role === 'user');
</script>

<div class="flex gap-3" class:flex-row-reverse={isUser}>
	<div
		class="shrink-0 h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold"
		class:bg-blue-600={isUser}
		class:bg-slate-700={!isUser}
	>
		{isUser ? 'U' : 'A'}
	</div>
	<div class="max-w-[80%] space-y-2">
		<div
			class="rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap"
			class:bg-blue-600={isUser}
			class:text-white={isUser}
			class:bg-slate-800={!isUser}
			class:text-slate-200={!isUser}
		>
			{message.content}
		</div>
		{#if meta}
			<div class="flex flex-wrap gap-1.5">
			<span
				class="inline-flex items-center rounded-full px-2 py-0.5 text-xs {meta.is_sensitive ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700 text-slate-400'}"
			>
				{meta.is_sensitive ? '🔒 ' + get(t)('demo.meta.sensitive') : '✅ ' + get(t)('demo.meta.safe')}
			</span>
				{#if meta.records.length > 0}
					{#each meta.records as record}
						<span class="inline-flex items-center rounded-full bg-amber-500/20 px-2 py-0.5 text-xs text-amber-400">
							{record.category}: {record.span}
						</span>
					{/each}
				{/if}
				<span class="inline-flex items-center rounded-full bg-slate-700 px-2 py-0.5 text-xs text-slate-400">
					{meta.route.endpoint} → {meta.policy_action}
				</span>
			</div>
		{/if}
	</div>
</div>
