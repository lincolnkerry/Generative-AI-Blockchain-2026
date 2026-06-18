<script lang="ts">
	import { t } from '$lib/i18n';
	import { LangToggle, Card, Badge } from '$lib/components/ui';

	const sections = [
		{ key: 'architecture', href: '/documentation/architecture', icon: '🏗️' },
		{ key: 'install', href: '/documentation/install', icon: '🚀' },
		{ key: 'logs', href: '/documentation/logs', icon: '📋' },
		{ key: 'cost', href: '/documentation/cost', icon: '💰' },
		{ key: 'security', href: '/documentation/security', icon: '🔒' },
		{ key: 'differentiation', href: '/documentation/differentiation', icon: '⚡' },
		{ key: 'smartening', href: '/documentation/smartening', icon: '🧠' },
		{ key: 'evidence', href: '/documentation/evidence', icon: '📊' },
	];
</script>

<svelte:head>
	<title>{$t('docs.title')} — Privacy Router</title>
</svelte:head>

<div class="min-h-screen bg-slate-950 text-slate-200">
	<header class="border-b border-slate-800 px-6 py-4">
		<div class="max-w-4xl mx-auto flex items-center justify-between">
			<a href="/" class="text-sm text-slate-400 hover:text-white transition">{$t('nav.back')}</a>
			<div class="flex items-center gap-3">
				<span class="text-xs text-slate-500">{$t('nav.docs')}</span>
				<LangToggle />
			</div>
		</div>
	</header>

	<main class="max-w-4xl mx-auto px-6 py-12 space-y-10">
		<div>
			<h1 class="text-3xl font-bold text-white mb-2">{$t('docs.title')}</h1>
			<p class="text-slate-400">{$t('docs.overview.desc')}</p>
		</div>

		<div class="grid gap-4 sm:grid-cols-2">
			{#each sections as s}
				<a
					href={s.href}
					class="group block rounded-xl border border-slate-800 bg-slate-900/50 p-6 transition hover:border-slate-700 hover:bg-slate-900"
				>
					<div class="text-2xl mb-3">{s.icon}</div>
					<h2 class="font-semibold text-white group-hover:text-blue-400 transition mb-1">
						{$t(`docs.${s.key}`)}
					</h2>
					<p class="text-sm text-slate-400">{$t(`docs.${s.key}.title`)}</p>
				</a>
			{/each}
		</div>

		<!-- Problem / Solution -->
		<div class="grid gap-4 sm:grid-cols-2">
			<Card>
				<div class="p-6">
					<div class="flex items-center gap-2 mb-3">
						<h3 class="font-semibold text-white">{$t('docs.overview.problem')}</h3>
						<Badge variant="danger">{$t('demo.meta.sensitive')}</Badge>
					</div>
					<p class="text-sm text-slate-400 leading-relaxed">{$t('docs.overview.problem.text')}</p>
				</div>
			</Card>
			<Card>
				<div class="p-6">
					<div class="flex items-center gap-2 mb-3">
						<h3 class="font-semibold text-white">{$t('docs.overview.solution')}</h3>
						<Badge variant="success">{$t('demo.meta.safe')}</Badge>
					</div>
					<p class="text-sm text-slate-400 leading-relaxed">{$t('docs.overview.solution.text')}</p>
				</div>
			</Card>
		</div>
	</main>
</div>
