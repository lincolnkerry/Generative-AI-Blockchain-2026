<script lang="ts">
	import { t } from '$lib/i18n';
	import { LangToggle } from '$lib/components/ui';

	const tiers = [
		{ tier: 'cloud', when: 'cloud.when', where: 'cloud.where', why: 'cloud.why' },
		{ tier: 'local', when: 'local.when', where: 'local.where', why: 'local.why' }
	];

	const breakdown = [
		{ component: 'SLM Extraction (Ministral 3B)', tier: 'docs.cost.cloud', usage: '2000 prompts × 500 tokens', unit: '$0.10/M', monthly: '$0.10' },
		{ component: 'SLM Critic', tier: 'docs.cost.cloud', usage: '2000 prompts × 200 tokens', unit: '$0.10/M', monthly: '$0.04' },
		{ component: 'Frontier LLM (Gemini Flash)', tier: 'docs.cost.cloud', usage: '200 prompts × 1000 tokens', unit: '$0.25/M', monthly: '$0.05' },
		{ component: 'Local LLM (qwen3:14b)', tier: 'docs.cost.local', usage: '200 prompts', unit: '$0.00', monthly: '$0.00' }
	];
</script>

<svelte:head>
	<title>Cost Analysis — Privacy Router</title>
</svelte:head>

<div class="min-h-screen bg-slate-950 text-slate-200">
	<header class="border-b border-slate-800 px-6 py-4">
		<div class="max-w-5xl mx-auto flex items-center justify-between">
			<a href="/documentation" class="text-sm text-slate-400 hover:text-white transition">← {$t('nav.docs')}</a>
			<div class="flex items-center gap-3">
				<span class="text-xs text-slate-500">{$t('docs.cost.title')}</span>
				<LangToggle />
			</div>
		</div>
	</header>

	<main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
		<h1 class="text-3xl font-bold text-white">{$t('docs.cost.title')}</h1>

		<!-- Two-Tier Routing -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">{$t('docs.cost.two_tier')}</h2>
			<p class="text-sm text-slate-400">{$t('docs.cost.two_tier.desc')}</p>
			<div class="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b border-slate-800 bg-slate-900">
							<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.cost.tier')}</th>
							<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.cost.when')}</th>
							<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.cost.where')}</th>
							<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.cost.why')}</th>
						</tr>
					</thead>
					<tbody class="text-slate-300">
						{#each tiers as row}
							<tr class="border-b border-slate-800/50">
								<td class="px-6 py-3">
									<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {row.tier === 'cloud' ? 'bg-blue-500/20 text-blue-400' : 'bg-emerald-500/20 text-emerald-400'}">
										{$t(`docs.cost.${row.tier}`)}
									</span>
								</td>
								<td class="px-6 py-3">{$t(`docs.cost.${row.when}`)}</td>
								<td class="px-6 py-3">{$t(`docs.cost.${row.where}`)}</td>
								<td class="px-6 py-3">{$t(`docs.cost.${row.why}`)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</section>

		<!-- Cost Breakdown -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">{$t('docs.cost.breakdown')}</h2>
			<div class="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b border-slate-800 bg-slate-900">
							<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.cost.component')}</th>
							<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.cost.tier')}</th>
							<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.cost.usage')}</th>
							<th class="px-6 py-3 text-right text-slate-400 font-medium">{$t('docs.cost.unit_cost')}</th>
							<th class="px-6 py-3 text-right text-slate-400 font-medium">{$t('docs.cost.monthly_cost')}</th>
						</tr>
					</thead>
					<tbody class="text-slate-300">
						{#each breakdown as row}
							<tr class="border-b border-slate-800/50">
								<td class="px-6 py-3 font-medium text-white">{row.component}</td>
								<td class="px-6 py-3">{$t(row.tier)}</td>
								<td class="px-6 py-3 text-slate-400">{row.usage}</td>
								<td class="px-6 py-3 text-right font-mono">{row.unit}</td>
								<td class="px-6 py-3 text-right font-mono">{row.monthly}</td>
							</tr>
						{/each}
					</tbody>
					<tfoot>
						<tr class="border-t-2 border-slate-700 bg-slate-900">
							<td colspan="4" class="px-6 py-3 font-semibold text-white">{$t('docs.cost.total')}</td>
							<td class="px-6 py-3 text-right font-mono font-bold text-emerald-400">$0.19/{$t('docs.cost.monthly').split(' ').pop()}</td>
						</tr>
					</tfoot>
				</table>
			</div>
		</section>

		<!-- vs Big Tech -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">{$t('docs.cost.vs_bigtech')}</h2>
			<p class="text-sm text-slate-400">{$t('docs.cost.vs_bigtech.desc')}</p>
			<div class="grid gap-4 sm:grid-cols-2">
				<div class="rounded-xl border border-slate-800 bg-slate-900/50 p-6 text-center">
					<p class="text-sm text-slate-400 mb-2">{$t('docs.cost.chatgpt_label')}</p>
					<p class="text-3xl font-bold text-red-400">{$t('docs.cost.chatgpt_price')}</p>
				</div>
				<div class="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-6 text-center">
					<p class="text-sm text-slate-400 mb-2">{$t('docs.cost.router_label')}</p>
					<p class="text-3xl font-bold text-emerald-400">{$t('docs.cost.router_price')}</p>
					<p class="text-xs text-emerald-500 mt-1">{$t('docs.cost.savings')}</p>
				</div>
			</div>
		</section>
	</main>
</div>
