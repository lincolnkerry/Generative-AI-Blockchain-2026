<script lang="ts">
	import { t } from '$lib/i18n';
	import { LangToggle } from '$lib/components/ui';

	const dimensions = ['pii', 'secrets', 'routing', 'masking', 'transparency', 'cost', 'agent'] as const;

	const advantages = [
		{ key: '1', icon: '🇰🇷' },
		{ key: '2', icon: '🔒' },
		{ key: '3', icon: '🔍' }
	];
</script>

<svelte:head>
	<title>Differentiation — Privacy Router</title>
</svelte:head>

<div class="min-h-screen bg-slate-950 text-slate-200">
	<header class="border-b border-slate-800 px-6 py-4">
		<div class="max-w-5xl mx-auto flex items-center justify-between">
			<a href="/documentation" class="text-sm text-slate-400 hover:text-white transition">← {$t('nav.docs')}</a>
			<div class="flex items-center gap-3">
				<span class="text-xs text-slate-500">{$t('docs.differentiation.title')}</span>
				<LangToggle />
			</div>
		</div>
	</header>

	<main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
		<h1 class="text-3xl font-bold text-white">{$t('docs.differentiation.title')}</h1>

		<!-- Comparison Table -->
		<section class="space-y-4">
			<div class="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b border-slate-800 bg-slate-900">
							<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.differentiation.dimension')}</th>
							<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.differentiation.bigtech')}</th>
							<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.differentiation.privacy_router')}</th>
						</tr>
					</thead>
					<tbody class="text-slate-300">
						{#each dimensions as dim}
							<tr class="border-b border-slate-800/50">
								<td class="px-6 py-3 font-medium text-white">{$t(`docs.differentiation.dims.${dim}`)}</td>
								<td class="px-6 py-3 text-slate-500">{$t(`docs.differentiation.dims.${dim}.bigtech`)}</td>
								<td class="px-6 py-3 text-emerald-400">{$t(`docs.differentiation.dims.${dim}.pr`)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</section>

		<!-- Key Advantages -->
		<section class="space-y-6">
			<h2 class="text-xl font-semibold text-white">{$t('docs.differentiation.advantages')}</h2>
			<div class="grid gap-4 sm:grid-cols-3">
				{#each advantages as adv}
					<div class="rounded-xl border border-slate-800 bg-slate-900/50 p-6 space-y-3">
						<div class="text-2xl">{adv.icon}</div>
						<h3 class="font-semibold text-white">{$t(`docs.differentiation.advantage.${adv.key}.title`)}</h3>
						<p class="text-sm text-slate-400 leading-relaxed">{$t(`docs.differentiation.advantage.${adv.key}.desc`)}</p>
					</div>
				{/each}
			</div>
		</section>
	</main>
</div>
