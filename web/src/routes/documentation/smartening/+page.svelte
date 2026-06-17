<script lang="ts">
	import { t } from '$lib/i18n';
	import { LangToggle, Card } from '$lib/components/ui';
</script>

<svelte:head>
	<title>{$t('docs.smartening.title')} — Privacy Router</title>
</svelte:head>

<div class="min-h-screen bg-slate-950 text-slate-200">
	<header class="border-b border-slate-800 px-6 py-4">
		<div class="max-w-4xl mx-auto flex items-center justify-between">
			<a href="/documentation" class="text-sm text-slate-400 hover:text-white transition">← {$t('docs.back')}</a>
			<LangToggle />
		</div>
	</header>

	<main class="max-w-4xl mx-auto px-6 py-12 space-y-12">
		<h1 class="text-3xl font-bold text-white">{$t('docs.smartening.title')}</h1>

		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">Two-Phase Extraction</h2>
			<Card>
				<div class="p-6 space-y-4">
					<p class="text-slate-400">The Extractor runs in two phases to improve detection accuracy:</p>
					<div class="grid gap-4 sm:grid-cols-2">
						<div class="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
							<h3 class="font-medium text-white mb-2">Phase 1: Extract</h3>
							<p class="text-sm text-slate-400">SLM applies contextual reasoning to detect sensitive spans with free-form category tags.</p>
						</div>
						<div class="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
							<h3 class="font-medium text-white mb-2">Phase 2: Critic</h3>
							<p class="text-sm text-slate-400">Second SLM pass reviews Phase 1, catches missed spans, verifies is_essential classification.</p>
						</div>
					</div>
				</div>
			</Card>
		</section>

		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">Measurable Improvement</h2>
			<Card>
				<div class="p-6 space-y-4">
					<div class="overflow-x-auto">
						<table class="w-full text-sm">
							<thead>
								<tr class="border-b border-slate-800">
									<th class="py-2 text-left text-slate-400">Metric</th>
									<th class="py-2 text-left text-slate-400">Single-pass</th>
									<th class="py-2 text-left text-slate-400">Two-phase</th>
								</tr>
							</thead>
							<tbody class="text-slate-300">
								<tr class="border-b border-slate-800/50"><td class="py-2">Miss rate (multi-span)</td><td>~15%</td><td>~3%</td></tr>
								<tr class="border-b border-slate-800/50"><td class="py-2">Business secrets detection</td><td>0%</td><td>100%</td></tr>
								<tr class="border-b border-slate-800/50"><td class="py-2">Research secrets detection</td><td>0%</td><td>100%</td></tr>
								<tr><td class="py-2">Inference cost</td><td>1x</td><td>~1.3x (same SLM)</td></tr>
							</tbody>
						</table>
					</div>
				</div>
			</Card>
		</section>

		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">Hallucination Filtering</h2>
			<Card>
				<div class="p-6">
					<p class="text-slate-400">The merge step verifies that each detected span actually exists in the original text. Spans that don't match are discarded as hallucinations.</p>
				</div>
			</Card>
		</section>
	</main>
</div>
