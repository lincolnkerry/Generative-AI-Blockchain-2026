<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		class?: string;
		children: Snippet;
	}

	let { class: cls = '', children }: Props = $props();
</script>

<div class="rounded-xl border border-slate-800 bg-slate-900/50 {cls}">
	{@render children()}
</div>
