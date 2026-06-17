<script lang="ts">
	import { Modal, Input, Button } from '$lib/components/ui';
	import { t } from '$lib/i18n';
	import { get } from 'svelte/store';

	interface Props {
		open: boolean;
		onclose: () => void;
		keyId: string;
		currentName: string;
		onsaved: () => void;
	}

	let { open = $bindable(false), onclose, keyId, currentName, onsaved }: Props = $props();

	let name = $state('');
	let loading = $state(false);

	$effect(() => {
		if (open) name = currentName;
	});

	async function handleSave() {
		loading = true;
		try {
			const res = await fetch(`/api/v1/keys/${keyId}`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ name })
			});
			if (res.ok) {
				onsaved();
				onclose();
			}
		} finally {
			loading = false;
		}
	}

	function onkeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') handleSave();
	}
</script>

<svelte:window {onkeydown} />

<Modal bind:open {onclose} title={$t("modal.rename.title")}>
	<Input bind:value={name} label={$t("modal.rename.name")} placeholder={$t("modal.rename.name")} />

	{#snippet footer()}
		<Button variant="secondary" onclick={onclose}>{$t("modal.rename.cancel")}</Button>
		<Button variant="primary" onclick={handleSave} disabled={loading || !name.trim()}>
			{loading ? get(t)('modal.rename.saving') : get(t)('modal.rename.save')}
		</Button>
	{/snippet}
</Modal>
