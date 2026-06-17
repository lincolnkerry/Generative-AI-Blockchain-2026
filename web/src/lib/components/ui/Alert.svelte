<script lang="ts">
	import type { Snippet } from 'svelte';

	type Variant = 'info' | 'success' | 'warning' | 'error';

	interface Props {
		variant?: Variant;
		children: Snippet;
		onclose?: () => void;
	}

	let { variant = 'info', children, onclose }: Props = $props();

	const variants: Record<Variant, string> = {
		info: 'border-blue-500/30 bg-blue-500/10 text-blue-300',
		success: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
		warning: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
		error: 'border-red-500/30 bg-red-500/10 text-red-300'
	};
</script>

<div class="flex items-start gap-3 rounded-lg border p-4 {variants[variant]}" role="alert">
	<div class="flex-1 text-sm">
		{@render children()}
	</div>
	{#if onclose}
		<button onclick={onclose} class="shrink-0 text-current opacity-50 hover:opacity-100 transition">
			✕
		</button>
	{/if}
</div>
