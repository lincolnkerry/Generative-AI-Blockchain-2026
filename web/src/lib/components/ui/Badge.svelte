<script lang="ts">
	import type { Snippet } from 'svelte';

	type Variant = 'default' | 'success' | 'warning' | 'danger' | 'info';

	interface Props {
		variant?: Variant;
		children: Snippet;
	}

	let { variant = 'default', children }: Props = $props();

	const variants: Record<Variant, string> = {
		default: 'bg-slate-700 text-slate-300',
		success: 'bg-emerald-500/20 text-emerald-400',
		warning: 'bg-amber-500/20 text-amber-400',
		danger: 'bg-red-500/20 text-red-400',
		info: 'bg-blue-500/20 text-blue-400'
	};
</script>

<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {variants[variant]}">
	{@render children()}
</span>
