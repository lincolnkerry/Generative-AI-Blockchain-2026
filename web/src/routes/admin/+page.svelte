<script lang="ts">
	import type { KeyOut, KeyCreated, ProviderOut, RouterSettings } from '$lib/types';
	import { keys as keysApi, providers as providersApi, settings as settingsApi } from '$lib/api';
	import { Button, Card, Select, Alert, LangToggle } from '$lib/components/ui';
	import { t } from '$lib/i18n';
	import { get } from 'svelte/store';
	import {
		KeyList,
		CreateKeyModal,
		ShowKeyModal,
		RenameKeyModal,
		BulkActionBar
	} from '$lib/components/admin';

	// ── State ───────────────────────────────────────────────────────────────
	let keys = $state<KeyOut[]>([]);
	let providers = $state<ProviderOut[]>([]);
	let settings = $state<RouterSettings | null>(null);
	let selectedIds = $state<Set<string>>(new Set());

	// Modal state
	let createOpen = $state(false);
	let showKeyOpen = $state(false);
	let createdKey = $state('');
	let renameOpen = $state(false);
	let renameKeyId = $state('');
	let renameCurrentName = $state('');

	// Alert state
	let alerts = $state<{ id: number; message: string; variant: 'success' | 'error' | 'warning' }[]>([]);
	let alertCounter = $state(0);

	// Settings form
	let extractorModel = $state('');
	let judgeModel = $state('');
	let routerModel = $state('');

	// ── Derived ─────────────────────────────────────────────────────────────
	let modelOptions = $derived(
		(settings?.models ?? []).map((m) => ({
			value: m.model_id,
			label: m.display_name ?? m.model_id
		}))
	);

	// ── Lifecycle ───────────────────────────────────────────────────────────
	async function loadAll() {
		try {
			const [k, p, s] = await Promise.all([keysApi.list(), providersApi.list(), settingsApi.get()]);
			keys = k;
			providers = p;
			settings = s;
			extractorModel = s.extractor?.model ?? '';
			judgeModel = s.judge?.model ?? '';
			routerModel = s.router?.model ?? '';
		} catch (e) {
			showAlert(e instanceof Error ? e.message : String(e), 'error');
		}
	}

	$effect(() => {
		loadAll();
	});

	// ── Helpers ─────────────────────────────────────────────────────────────
	function showAlert(message: string, variant: 'success' | 'error' | 'warning' = 'success') {
		const id = ++alertCounter;
		alerts = [...alerts, { id, message, variant }];
		setTimeout(() => {
			alerts = alerts.filter((a) => a.id !== id);
		}, 4000);
	}

	// ── Key actions ─────────────────────────────────────────────────────────
	function handleToggleSelect(id: string, checked: boolean) {
		const next = new Set(selectedIds);
		checked ? next.add(id) : next.delete(id);
		selectedIds = next;
	}

	function handleToggleSelectAll(checked: boolean) {
		selectedIds = checked ? new Set(keys.map((k) => k.id)) : new Set();
	}

	async function handleToggleActive(id: string) {
		const key = keys.find((k) => k.id === id);
		if (!key) return;
		try {
			await keysApi.update(id, { is_active: !key.is_active });
			keys = keys.map((k) => (k.id === id ? { ...k, is_active: !k.is_active } : k));
			showAlert(`${key.name} ${get(t)(key.is_active ? 'alert.toggle_deactivated' : 'alert.toggle_activated')}`);
		} catch (e) {
			showAlert(e instanceof Error ? e.message : String(e), 'error');
		}
	}

	async function handleRenew(id: string) {
		try {
			const res = await keysApi.renew(id);
			createdKey = res.api_key;
			showKeyOpen = true;
			await loadAll();
			showAlert(get(t)('alert.key_renewed'));
		} catch (e) {
			showAlert(e instanceof Error ? e.message : String(e), 'error');
		}
	}

	async function handleDelete(id: string) {
		try {
			await keysApi.delete(id);
			keys = keys.filter((k) => k.id !== id);
			selectedIds = new Set([...selectedIds].filter((sid) => sid !== id));
			showAlert(get(t)('alert.key_deleted'));
		} catch (e) {
			showAlert(e instanceof Error ? e.message : String(e), 'error');
		}
	}

	function handleRename(id: string, currentName: string) {
		renameKeyId = id;
		renameCurrentName = currentName;
		renameOpen = true;
	}

	async function handleCopyPrefix(prefix: string, btn: HTMLButtonElement) {
		try {
			await navigator.clipboard.writeText(prefix + '…');
			btn.textContent = '✓';
			setTimeout(() => (btn.textContent = '📋'), 1500);
		} catch { /* noop */ }
	}

	// ── Bulk actions ────────────────────────────────────────────────────────
	async function handleBulkActivate() {
		try {
			const res = await keysApi.bulkToggle([...selectedIds], true);
			keys = keys.map((k) => (selectedIds.has(k.id) ? { ...k, is_active: true } : k));
			selectedIds = new Set();
			showAlert(`${res.updated} ${get(t)('alert.keys_activated')}`);
		} catch (e) {
			showAlert(e instanceof Error ? e.message : String(e), 'error');
		}
	}

	async function handleBulkDeactivate() {
		try {
			const res = await keysApi.bulkToggle([...selectedIds], false);
			keys = keys.map((k) => (selectedIds.has(k.id) ? { ...k, is_active: false } : k));
			selectedIds = new Set();
			showAlert(`${res.updated} ${get(t)('alert.keys_deactivated')}`);
		} catch (e) {
			showAlert(e instanceof Error ? e.message : String(e), 'error');
		}
	}

	let bulkDeleteConfirm = $state(false);

	async function handleBulkDelete() {
		try {
			const res = await keysApi.bulkDelete([...selectedIds]);
			keys = keys.filter((k) => !selectedIds.has(k.id));
			selectedIds = new Set();
			bulkDeleteConfirm = false;
			showAlert(`${res.updated} ${get(t)('alert.keys_bulk_deleted')}`);
		} catch (e) {
			showAlert(e instanceof Error ? e.message : String(e), 'error');
		}
	}

	// ── Created key callback ────────────────────────────────────────────────
	function handleKeyCreated(data: KeyCreated) {
		createdKey = data.api_key;
		showKeyOpen = true;
		loadAll();
		showAlert(get(t)('alert.key_created'));
	}

	// ── Settings save ───────────────────────────────────────────────────────
	async function handleSaveSettings() {
		try {
			await settingsApi.save({
				extractor: { model: extractorModel },
				judge: { model: judgeModel },
				router: { model: routerModel }
			});
			showAlert(get(t)('alert.settings_saved'));
		} catch (e) {
			showAlert(e instanceof Error ? e.message : String(e), 'error');
		}
	}
</script>
<svelte:head>
	<title>{$t('admin.title')} — Privacy Router</title>
</svelte:head>

<div class="min-h-screen bg-slate-950 text-slate-200">
	<!-- Header -->
	<header class="border-b border-slate-800 px-6 py-4">
		<div class="max-w-5xl mx-auto flex items-center justify-between">
			<a href="/" class="text-sm text-slate-400 hover:text-white transition">{$t('nav.back')}</a>
			<div class="flex items-center gap-3">
				<span class="text-xs text-slate-500">{$t('nav.admin')}</span>
				<LangToggle />
			</div>
		</div>
	</header>

	<main class="max-w-5xl mx-auto px-6 py-8 space-y-8">
		<!-- Alerts -->
		<div class="space-y-2">
			{#each alerts as alert (alert.id)}
				<Alert variant={alert.variant} onclose={() => (alerts = alerts.filter((a) => a.id !== alert.id))}>
					{alert.message}
				</Alert>
			{/each}
		</div>

		<!-- Warning -->
		<Alert variant="warning">
			{$t('admin.warning')}
		</Alert>

		<!-- Keys section -->
		<section>
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-xl font-bold text-white">{$t('admin.keys.title')}</h2>
				<Button onclick={() => (createOpen = true)}>+ {$t('admin.keys.create')}</Button>
			</div>

			<BulkActionBar
				selectedCount={selectedIds.size}
				onActivate={handleBulkActivate}
				onDeactivate={handleBulkDeactivate}
				onDelete={() => (bulkDeleteConfirm = true)}
				onClear={() => (selectedIds = new Set())}
			/>

			<div class="mt-4">
				<KeyList
					{keys}
					{selectedIds}
					onToggleSelect={handleToggleSelect}
					onToggleSelectAll={handleToggleSelectAll}
					onToggleActive={handleToggleActive}
					onRenew={handleRenew}
					onDelete={handleDelete}
					onRename={handleRename}
					onCopyPrefix={handleCopyPrefix}
				/>
			</div>
		</section>

		<!-- Settings section -->
		<Card>
			<div class="p-6 space-y-4">
				<h2 class="text-xl font-bold text-white">{$t('admin.settings.title')}</h2>
				<div class="grid gap-4 sm:grid-cols-3">
					<Select bind:value={extractorModel} options={modelOptions} label="Extractor" />
					<Select bind:value={judgeModel} options={modelOptions} label="Judge" />
					<Select bind:value={routerModel} options={modelOptions} label="Router" />
				</div>
				<div class="flex justify-end">
					<Button onclick={handleSaveSettings}>{$t('admin.settings.save')}</Button>
				</div>
			</div>
		</Card>
	</main>
</div>

<!-- Modals -->
<CreateKeyModal bind:open={createOpen} onclose={() => (createOpen = false)} {providers} oncreated={handleKeyCreated} />
<ShowKeyModal bind:open={showKeyOpen} onclose={() => (showKeyOpen = false)} apiKey={createdKey} />
<RenameKeyModal
	bind:open={renameOpen}
	onclose={() => (renameOpen = false)}
	keyId={renameKeyId}
	currentName={renameCurrentName}
	onsaved={loadAll}
/>

<!-- Bulk delete confirmation -->
{#if bulkDeleteConfirm}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" role="dialog" aria-modal="true">
		<div class="w-full max-w-md rounded-xl border border-slate-700 bg-slate-900 p-6 shadow-2xl">
			<h3 class="text-lg font-semibold text-white mb-4">{get(t)('admin.keys.delete_confirm')}</h3>
			<p class="text-sm text-slate-400 mb-4">
				{selectedIds.size} {get(t)('admin.keys.delete_confirm_msg')}
			</p>
			<ul class="mb-6 space-y-1">
				{#each keys.filter((k) => selectedIds.has(k.id)) as key (key.id)}
					<li class="text-sm text-slate-300">• {key.name} ({key.prefix}…)</li>
				{/each}
			</ul>
			<div class="flex justify-end gap-3">
				<Button variant="secondary" onclick={() => (bulkDeleteConfirm = false)}>{get(t)("common.cancel")}</Button>
				<Button variant="danger" onclick={handleBulkDelete}>{get(t)("common.delete")}</Button>
			</div>
		</div>
	</div>
{/if}
