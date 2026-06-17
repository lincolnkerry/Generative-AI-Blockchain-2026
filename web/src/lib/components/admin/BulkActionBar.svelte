<script lang="ts">
	import { Button } from '$lib/components/ui';
	import { t } from '$lib/i18n';

	interface Props {
		selectedCount: number;
		onActivate: () => void;
		onDeactivate: () => void;
		onDelete: () => void;
		onClear: () => void;
	}

	let { selectedCount, onActivate, onDeactivate, onDelete, onClear }: Props = $props();
</script>

{#if selectedCount > 0}
	<div class="flex items-center gap-4 rounded-lg border border-blue-500/30 bg-blue-500/10 px-4 py-3">
		<span class="text-sm text-blue-300">
			{selectedCount} {$t("admin.keys.selected")}
		</span>
		<div class="flex gap-2">
			<Button variant="secondary" size="sm" onclick={onActivate}>{$t("admin.keys.bulk_activate")}</Button>
			<Button variant="secondary" size="sm" onclick={onDeactivate}>{$t("admin.keys.bulk_deactivate")}</Button>
			<Button variant="danger" size="sm" onclick={onDelete}>{$t("admin.keys.bulk_delete")}</Button>
		</div>
		<button
			class="ml-auto text-xs text-slate-400 hover:text-white transition cursor-pointer"
			onclick={onClear}
		>
			{$t("admin.keys.clear_selection")}
		</button>
	</div>
{/if}
