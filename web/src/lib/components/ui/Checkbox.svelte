<script lang="ts">
	interface Props {
		checked?: boolean;
		label?: string;
		disabled?: boolean;
		onchange?: (checked: boolean) => void;
	}

	let {
		checked = $bindable(false),
		label,
		disabled = false,
		onchange
	}: Props = $props();
</script>

<label class="inline-flex items-center gap-2 cursor-pointer select-none" class:opacity-50={disabled}>
	<input
		type="checkbox"
		bind:checked
		{disabled}
		onchange={() => onchange?.(checked)}
		class="h-4 w-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-900"
	/>
	{#if label}
		<span class="text-sm text-slate-300">{label}</span>
	{/if}
</label>
