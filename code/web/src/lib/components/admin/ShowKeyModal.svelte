<script lang="ts">
	import { Modal, Button } from '$lib/components/ui';
	import { t } from '$lib/i18n';
	import { get } from 'svelte/store';

	interface Props {
		open: boolean;
		onclose: () => void;
		apiKey: string;
	}

	let { open = $bindable(false), onclose, apiKey }: Props = $props();

	let copied = $state(false);

	async function copyKey() {
		try {
			await navigator.clipboard.writeText(apiKey);
			copied = true;
			setTimeout(() => (copied = false), 2000);
		} catch {
			const ta = document.createElement('textarea');
			ta.value = apiKey;
			document.body.appendChild(ta);
			ta.select();
			document.execCommand('copy');
			document.body.removeChild(ta);
			copied = true;
			setTimeout(() => (copied = false), 2000);
		}
	}
</script>

<Modal bind:open {onclose} title={$t("modal.show.title")}>
	<div class="space-y-4">
		<p class="text-sm text-slate-400">
			{$t("modal.show.message")}
		</p>
		<div class="flex items-center gap-2">
			<code class="flex-1 rounded-lg bg-slate-800 px-3 py-2 text-sm text-emerald-400 font-mono break-all">
				{apiKey}
			</code>
			<Button variant="secondary" size="sm" onclick={copyKey}>
				{copied ? '✓ ' + get(t)('modal.show.copied') : get(t)('modal.show.copy')}
			</Button>
		</div>
	</div>

	{#snippet footer()}
		<Button variant="primary" onclick={onclose}>{$t("modal.show.confirm")}</Button>
	{/snippet}
</Modal>
