<script lang="ts">
	interface Option {
		value: string;
		label: string;
	}

	interface Props {
		value?: string;
		options: Option[];
		label?: string;
		disabled?: boolean;
		onchange?: (e: Event) => void;
	}

	let {
		value = $bindable(''),
		options,
		label,
		disabled = false,
		onchange
	}: Props = $props();
</script>

<div class="space-y-1.5">
	{#if label}
		<label class="block text-sm font-medium text-slate-300">{label}</label>
	{/if}
	<select
		{disabled}
		bind:value
		{onchange}
		class="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 transition focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
	>
		{#each options as opt}
			<option value={opt.value}>{opt.label}</option>
		{/each}
	</select>
</div>
