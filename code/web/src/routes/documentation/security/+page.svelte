<script lang="ts">
	import { t } from '$lib/i18n';
	import { LangToggle } from '$lib/components/ui';

	const threatModel = [
		{ component: 'Extractor', threat: 'Sensitive data sent to cloud', mitigation: 'Runs locally' },
		{ component: 'Masking', threat: 'Placeholders reversible', mitigation: 'UID-based [TAG#hash]' },
		{ component: 'Storage', threat: 'Plaintext storage', mitigation: 'Fernet encryption' },
		{ component: 'Audit', threat: 'No visibility', mitigation: 'Full logging' },
		{ component: 'Session', threat: 'State leakage', mitigation: 'Stateless, cache by chat_id' }
	];

	const adrs = [
		{ id: '001', href: 'https://github.com/lincolnkerry/Generative-AI-Blockchain-2026/blob/main/docs/adr/ADR-001-no-auth-on-key-admin-endpoints.md' },
		{ id: '002', href: 'https://github.com/lincolnkerry/Generative-AI-Blockchain-2026/blob/main/docs/adr/ADR-002-public-admin-endpoints-for-standalone-ui.md' },
		{ id: '003', href: 'https://github.com/lincolnkerry/Generative-AI-Blockchain-2026/blob/main/docs/adr/ADR-003-sqlite-as-default-database.md' },
		{ id: '004', href: 'https://github.com/lincolnkerry/Generative-AI-Blockchain-2026/blob/main/docs/adr/ADR-004-keep-deprecated-test-mcp-tools.md' }
	];
</script>

<svelte:head>
	<title>Privacy & Security — Privacy Router</title>
</svelte:head>

<div class="min-h-screen bg-slate-950 text-slate-200">
	<header class="border-b border-slate-800 px-6 py-4">
		<div class="max-w-5xl mx-auto flex items-center justify-between">
			<a href="/documentation" class="text-sm text-slate-400 hover:text-white transition">← {$t('nav.docs')}</a>
			<div class="flex items-center gap-3">
				<span class="text-xs text-slate-500">{$t('docs.security.title')}</span>
				<LangToggle />
			</div>
		</div>
	</header>

	<main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
		<h1 class="text-3xl font-bold text-white">{$t('docs.security.title')}</h1>

		<!-- Data Flow -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">{$t('docs.security.dataflow')}</h2>
			<p class="text-sm text-slate-400">{$t('docs.security.dataflow.desc')}</p>
			<div class="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
				<pre class="text-sm font-mono text-slate-300 leading-relaxed overflow-x-auto whitespace-pre">{`┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Agent      │────▶│  Extractor   │────▶│    Judge     │
│  (prompt)    │     │  (on-device) │     │  (on-device) │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                         ┌─────────────────────┤
                         ▼                     ▼
                  ┌─────────────┐     ┌─────────────┐
                  │    Masker    │     │ Local LLM    │
                  │  (on-device) │     │ (on-device)  │
                  └──────┬──────┘     └─────────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  Cloud LLM   │
                  │ (masked only)│
                  └─────────────┘`}</pre>
			</div>
		</section>

		<!-- Threat Model -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">{$t('docs.security.threat_model')}</h2>
			<div class="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b border-slate-800 bg-slate-900">
							<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.security.component')}</th>
							<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.security.threat')}</th>
							<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.security.mitigation')}</th>
						</tr>
					</thead>
					<tbody class="text-slate-300">
						{#each threatModel as row}
							<tr class="border-b border-slate-800/50">
								<td class="px-6 py-3 font-medium text-white">{row.component}</td>
								<td class="px-6 py-3 text-red-400/80">{row.threat}</td>
								<td class="px-6 py-3 text-emerald-400/80">{row.mitigation}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</section>

		<!-- Encryption -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">{$t('docs.security.encryption')}</h2>
			<div class="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
				<p class="text-sm text-slate-400">{$t('docs.security.encryption.desc')}</p>
			</div>
		</section>

		<!-- ADR Links -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">{$t('docs.security.adr')}</h2>
			<p class="text-sm text-slate-400">{$t('docs.security.adr.desc')}</p>
			<div class="grid gap-3 sm:grid-cols-2">
				{#each adrs as adr}
					<a href={adr.href} target="_blank" rel="noopener noreferrer" class="rounded-xl border border-slate-800 bg-slate-900/50 p-5 hover:border-slate-700 transition group">
						<h3 class="font-medium text-white group-hover:text-blue-400 transition mb-1">{$t(`docs.security.adr.${adr.id}`)}</h3>
						<p class="text-sm text-slate-400">{$t(`docs.security.adr.${adr.id}.desc`)}</p>
					</a>
				{/each}
			</div>
		</section>
	</main>
</div>
