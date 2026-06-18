<script lang="ts">
	import { t } from '$lib/i18n';
	import { LangToggle, Card, Badge } from '$lib/components/ui';

	let copied = $state('');

	function copy(text: string, id: string) {
		navigator.clipboard.writeText(text);
		copied = id;
		setTimeout(() => { if (copied === id) copied = ''; }, 2000);
	}

	const dockerScenarios = [
		{
			id: 'minimal',
			labelKey: 'docs.install.docker.minimal',
			cmd: 'docker compose up -d',
			files: 'docker-compose.yml',
		},
		{
			id: 'hermes',
			labelKey: 'docs.install.docker.hermes',
			cmd: 'docker compose up -d',
			files: 'docker-compose.yml',
		},
	];

	const curlCmd = 'curl -X POST http://localhost:8787/api/keys \\\n  -H "Content-Type: application/json" \\\n  -d \'{"name": "my-app"}\'';


	const accessPoints = [
		{ endpoint: '/', descKey: 'docs.install.access.landing' },
		{ endpoint: '/demo', descKey: 'docs.install.access.demo' },
		{ endpoint: '/admin', descKey: 'docs.install.access.admin' },
		{ endpoint: '/documentation', descKey: 'docs.install.access.docs' },
		{ endpoint: '/v1/chat/completions', descKey: 'docs.install.access.api' },
	];
</script>

<svelte:head>
	<title>{$t('docs.install.title')} — Privacy Router</title>
</svelte:head>

<div class="min-h-screen bg-slate-950 text-slate-200">
	<header class="border-b border-slate-800 px-6 py-4">
		<div class="max-w-5xl mx-auto flex items-center justify-between">
			<a href="/documentation" class="text-sm text-slate-400 hover:text-white transition">{$t('docs.back')}</a>
			<div class="flex items-center gap-3">
				<span class="text-xs text-slate-500">{$t('docs.install')}</span>
				<LangToggle />
			</div>
		</div>
	</header>

	<main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
		<div>
			<h1 class="text-3xl font-bold text-white mb-2">{$t('docs.install.title')}</h1>
		</div>

		<!-- Docker Compose -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white flex items-center gap-2">
				{$t('docs.install.docker')}
				<Badge variant="info">Recommended</Badge>
			</h2>

			<div class="space-y-4">
				{#each dockerScenarios as s}
					<Card>
						<div class="p-6">
							<h3 class="font-medium text-white mb-3">{$t(s.labelKey)}</h3>
							<p class="text-xs text-slate-500 mb-2">{s.files}</p>
							<div class="relative group">
								<pre class="rounded-lg bg-slate-950 border border-slate-800 px-4 py-3 text-sm text-emerald-400 overflow-x-auto font-mono">{s.cmd}</pre>
								<button
									onclick={() => copy(s.cmd, s.id)}
									class="absolute top-2 right-2 rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-400 opacity-0 group-hover:opacity-100 transition hover:text-white cursor-pointer"
								>
									{copied === s.id ? '✓' : $t('docs.install.copy')}
								</button>
							</div>
						</div>
					</Card>
				{/each}
			</div>
		</section>

		<!-- Local Development -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">{$t('docs.install.local')}</h2>

			<Card>
				<div class="p-6 space-y-6">
					<!-- Step 1 -->
					<div>
						<div class="flex items-center gap-2 mb-3">
							<span class="flex items-center justify-center h-6 w-6 rounded-full bg-blue-500/20 text-blue-400 text-xs font-bold">1</span>
							<h3 class="font-medium text-white">{$t('docs.install.local.step1')}</h3>
						</div>
						<div class="relative group">
							<pre class="rounded-lg bg-slate-950 border border-slate-800 px-4 py-3 text-sm text-emerald-400 overflow-x-auto font-mono">pip install -e ".[dev]"</pre>
							<button
								onclick={() => copy('pip install -e ".[dev]"', 'pip')}
								class="absolute top-2 right-2 rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-400 opacity-0 group-hover:opacity-100 transition hover:text-white cursor-pointer"
							>
								{copied === 'pip' ? '✓' : $t('docs.install.copy')}
							</button>
						</div>
					</div>

					<!-- Step 2 -->
					<div>
						<div class="flex items-center gap-2 mb-3">
							<span class="flex items-center justify-center h-6 w-6 rounded-full bg-blue-500/20 text-blue-400 text-xs font-bold">2</span>
							<h3 class="font-medium text-white">{$t('docs.install.local.step2')}</h3>
						</div>
						<div class="relative group">
							<pre class="rounded-lg bg-slate-950 border border-slate-800 px-4 py-3 text-sm text-emerald-400 overflow-x-auto font-mono">python -m server</pre>
							<button
								onclick={() => copy('python -m server', 'run')}
								class="absolute top-2 right-2 rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-400 opacity-0 group-hover:opacity-100 transition hover:text-white cursor-pointer"
							>
								{copied === 'run' ? '✓' : $t('docs.install.copy')}
							</button>
						</div>
					</div>
				</div>
			</Card>
		</section>

		<!-- Access Points -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">{$t('docs.install.access')}</h2>

			<Card>
				<div class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b border-slate-800">
								<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.install.access.endpoint')}</th>
								<th class="px-6 py-3 text-left text-slate-400 font-medium">{$t('docs.install.access.description')}</th>
							</tr>
						</thead>
						<tbody class="text-slate-300">
							{#each accessPoints as ap, i}
								<tr class={i < accessPoints.length - 1 ? 'border-b border-slate-800/50' : ''}>
									<td class="px-6 py-3">
										<code class="text-blue-400 font-mono text-xs">{ap.endpoint}</code>
									</td>
									<td class="px-6 py-3">{$t(ap.descKey)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</Card>
		</section>

		<!-- API Key Creation -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">{$t('docs.install.apikey')}</h2>

			<Card>
				<div class="p-6 space-y-4">
					<p class="text-sm text-slate-400">{$t('docs.install.apikey.desc')}</p>

					<div class="relative group">
						<pre class="rounded-lg bg-slate-950 border border-slate-800 px-4 py-3 text-sm text-emerald-400 overflow-x-auto font-mono">{curlCmd}</pre>
						<button
							onclick={() => copy(curlCmd, 'curl')}
							class="absolute top-2 right-2 rounded-md border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-400 opacity-0 group-hover:opacity-100 transition hover:text-white cursor-pointer"
						>
							{copied === 'curl' ? '✓' : $t('docs.install.copy')}
						</button>
					</div>

					<p class="text-xs text-slate-500">
						Alternatively, use the <a href="/admin" class="text-blue-400 hover:text-blue-300 transition">{$t('landing.card.admin')}</a> to create keys via the UI.
					</p>
				</div>
			</Card>
		</section>
	</main>
</div>
