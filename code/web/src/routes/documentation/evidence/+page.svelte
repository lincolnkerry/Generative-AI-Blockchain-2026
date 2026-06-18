<script lang="ts">
	import { t } from '$lib/i18n';
	import { LangToggle, Card } from '$lib/components/ui';

	const evidenceItems = [
		{ category: 'Usage Logs', items: [
			{ name: 'Usage Log (Markdown)', path: '/usage-log/USAGE_LOG.md' },
			{ name: 'DB Logs (JSON)', path: '/usage-log/db-logs.json' },
		]},
		{ category: 'Architecture Diagrams', items: [
			{ name: 'Pipeline Overview', path: '/diagrams/mermaid/pipeline.png' },
			{ name: 'System Architecture', path: '/diagrams/mermaid/architecture.png' },
			{ name: 'Two-Tier Stack', path: '/diagrams/mermaid/three-tier.png' },
		]},
		{ category: 'Architecture Decisions', items: [
			{ name: 'ADR-001: No Auth on Key Endpoints', path: '/docs/adr/ADR-001-no-auth-on-key-admin-endpoints.md' },
			{ name: 'ADR-002: Public Admin Endpoints', path: '/docs/adr/ADR-002-public-admin-endpoints-for-standalone-ui.md' },
			{ name: 'ADR-003: SQLite as Default', path: '/docs/adr/ADR-003-sqlite-as-default-database.md' },
			{ name: 'ADR-004: Keep Deprecated Test MCP', path: '/docs/adr/ADR-004-keep-deprecated-test-mcp-tools.md' },
		]},
		{ category: 'Evaluation', items: [
			{ name: 'Ground Truth Dataset', path: '/docs/ground_truth.json' },
			{ name: 'Audit Report', path: '/docs/AUDIT_REPORT.md' },
			{ name: 'Experiment Results', path: '/docs/developments/REPORT.md' },
		]},
	];
</script>

<svelte:head>
	<title>{$t('docs.evidence.title')} — Privacy Router</title>
</svelte:head>

<div class="min-h-screen bg-slate-950 text-slate-200">
	<header class="border-b border-slate-800 px-6 py-4">
		<div class="max-w-4xl mx-auto flex items-center justify-between">
			<a href="/documentation" class="text-sm text-slate-400 hover:text-white transition">← {$t('docs.back')}</a>
			<LangToggle />
		</div>
	</header>

	<main class="max-w-4xl mx-auto px-6 py-12 space-y-12">
		<h1 class="text-3xl font-bold text-white">{$t('docs.evidence.title')}</h1>
		<p class="text-slate-400">All claims are backed by logs, diagrams, measurements, and source code.</p>

		{#each evidenceItems as section}
			<section class="space-y-4">
				<h2 class="text-xl font-semibold text-white">{section.category}</h2>
				<div class="rounded-xl border border-slate-800 overflow-hidden">
					<table class="w-full text-sm">
						<tbody>
							{#each section.items as item, i}
								<tr class="border-b border-slate-800/50 hover:bg-slate-800/30 transition {i % 2 === 0 ? 'bg-slate-900/50' : ''}">
									<td class="px-4 py-3 text-slate-300">{item.name}</td>
									<td class="px-4 py-3 text-right">
										<a href={item.path} target="_blank" class="text-blue-400 hover:text-blue-300 text-xs">
											View →
										</a>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>
		{/each}
	</main>
</div>
