<script lang="ts">
	import type { Snippet } from 'svelte';

	type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';
	type Size = 'sm' | 'md' | 'lg';

	interface Props {
		variant?: Variant;
		size?: Size;
		disabled?: boolean;
		type?: 'button' | 'submit' | 'reset';
		onclick?: (e: MouseEvent) => void;
		children: Snippet;
	}

	let {
		variant = 'primary',
		size = 'md',
		disabled = false,
		type = 'button',
		onclick,
		children
	}: Props = $props();
</script>

<button
	{type}
	{disabled}
	class="inline-flex items-center justify-center font-medium rounded-lg transition focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:opacity-50 disabled:cursor-not-allowed
		{variant === 'primary' ? 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500' : ''}
		{variant === 'secondary' ? 'bg-slate-800 text-slate-200 hover:bg-slate-700 focus:ring-slate-500 border border-slate-700' : ''}
		{variant === 'ghost' ? 'text-slate-400 hover:text-white hover:bg-slate-800 focus:ring-slate-500' : ''}
		{variant === 'danger' ? 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500' : ''}
		{size === 'sm' ? 'px-3 py-1.5 text-xs' : ''}
		{size === 'md' ? 'px-4 py-2 text-sm' : ''}
		{size === 'lg' ? 'px-6 py-3 text-base' : ''}"
	onclick={onclick}
>
	{@render children()}
</button>
