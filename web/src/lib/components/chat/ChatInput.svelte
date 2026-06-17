<script lang="ts">
	import { Button } from '$lib/components/ui';
	import { t } from '$lib/i18n';

	interface Props {
		onsend: (text: string) => void;
		disabled?: boolean;
	}

	let { onsend, disabled = false }: Props = $props();

	let text = $state('');

	function handleSubmit() {
		const trimmed = text.trim();
		if (!trimmed || disabled) return;
		onsend(trimmed);
		text = '';
	}

	function onkeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit();
		}
	}
</script>

<div class="flex gap-3">
	<textarea
		bind:value={text}
		{onkeydown}
		{disabled}
		placeholder={$t("demo.input.placeholder")}
		rows="1"
		class="flex-1 resize-none rounded-xl border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
	></textarea>
	<Button onclick={handleSubmit} disabled={disabled || !text.trim()}>
		{$t("demo.input.send")}
	</Button>
</div>
