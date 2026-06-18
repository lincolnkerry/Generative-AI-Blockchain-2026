<script lang="ts">
	import { t } from '$lib/i18n';
	import { LangToggle } from '$lib/components/ui';

	const diagrams = [
		{ src: '/diagrams/mermaid/architecture.png', title: 'System Architecture (Mermaid)', desc: 'Full system architecture with agent integration' },
		{ src: '/diagrams/00_full_pipeline.png', title: 'Full Pipeline', desc: 'End-to-end Extract → Judge → Router pipeline' },
		{ src: '/diagrams/01_system_overview.png', title: 'System Overview', desc: 'High-level component architecture' },
		{ src: '/diagrams/02_pipeline_detail.png', title: 'Pipeline Detail', desc: 'Detailed extraction and routing logic' },
		{ src: '/diagrams/03_integration_ecosystem.png', title: 'Integration Ecosystem', desc: 'Hermes, OpenClaw, MCP integration' },
		{ src: '/diagrams/conceptual_architecture.png', title: 'Conceptual Architecture', desc: 'Conceptual data flow diagram' },
	];
</script>

<svelte:head>
	<title>Architecture — Privacy Router</title>
</svelte:head>

<div class="min-h-screen bg-slate-950 text-slate-200">
	<header class="border-b border-slate-800 px-6 py-4">
		<div class="max-w-5xl mx-auto flex items-center justify-between">
			<a href="/documentation" class="text-sm text-slate-400 hover:text-white transition">← Docs</a>
			<div class="flex items-center gap-3">
				<span class="text-xs text-slate-500">Architecture</span>
				<LangToggle />
			</div>
		</div>
	</header>

	<main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
		<h1 class="text-3xl font-bold text-white">Architecture</h1>

		<!-- Pipeline Overview -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">Pipeline Overview</h2>
			<div class="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
				<img src="/diagrams/mermaid/pipeline.png" alt="Pipeline Overview" class="w-full" loading="lazy" />
			</div>
		</section>

		<!-- Two-Tier Stack -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">Two-Tier Stack</h2>
			<div class="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
				<img src="/diagrams/mermaid/three-tier.png" alt="Two-Tier Stack" class="w-full" loading="lazy" />
			</div>
		</section>

		<!-- Diagrams -->
		<section class="space-y-6">
			<h2 class="text-xl font-semibold text-white">Diagrams</h2>
			{#each diagrams as d}
				<div class="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
					<div class="p-6">
						<h3 class="font-medium text-white mb-1">{d.title}</h3>
						<p class="text-sm text-slate-400">{d.desc}</p>
					</div>
					<img src={d.src} alt={d.title} class="w-full" loading="lazy" />
				</div>
			{/each}
		</section>

		<!-- Component Map -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">Component Map</h2>
			<div class="grid gap-4 sm:grid-cols-2">
				<div class="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
					<h3 class="font-medium text-white mb-2">agents/</h3>
					<ul class="text-sm text-slate-400 space-y-1">
						<li><code class="text-blue-400">extractor/</code> — SLM-based PII/context detection</li>
						<li><code class="text-blue-400">judge/</code> — Policy engine</li>
						<li><code class="text-blue-400">router/</code> — Orchestration + routing</li>
						<li><code class="text-blue-400">masker/</code> — Masking, hydration, contract</li>
					</ul>
				</div>
				<div class="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
					<h3 class="font-medium text-white mb-2">server/</h3>
					<ul class="text-sm text-slate-400 space-y-1">
						<li><code class="text-blue-400">api/routes/</code> — FastAPI endpoints</li>
						<li><code class="text-blue-400">mcp/</code> — MCP server (process tool)</li>
						<li><code class="text-blue-400">adapters/</code> — LLM provider adapters</li>
					</ul>
				</div>
			</div>
		</section>
	</main>
</div>
