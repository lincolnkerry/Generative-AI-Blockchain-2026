<script lang="ts">
	import { t } from '$lib/i18n';
	import { LangToggle } from '$lib/components/ui';

	// Current data: 46 real logs from Privacy Router DB
	const summary = {
		total: 46,
		sensitive: 31,
		safe: 15,
		routedLocal: 9,
		maskedSent: 22,
		passThrough: 15
	};

	const logEntries = [
		{ ts: '2026-06-17 03:52:53', sensitive: true, action: 'local_api', records: 5, desc: 'Research paper review with PII', descKo: 'PII 포함 논문 리뷰' },
		{ ts: '2026-06-17 03:53:39', sensitive: true, action: 'local_api', records: 6, desc: 'Business meeting preparation', descKo: '사업 미팅 준비' },
		{ ts: '2026-06-17 03:53:46', sensitive: false, action: 'external_api', records: 0, desc: 'Safe technical question', descKo: '안전한 기술 질문' },
		{ ts: '2026-06-17 03:54:07', sensitive: true, action: 'external_api', records: 5, desc: 'Research notes with unpublished data', descKo: '미공개 데이터 포함 연구 노트' },
		{ ts: '2026-06-17 03:54:13', sensitive: false, action: 'external_api', records: 0, desc: 'Safe technical question', descKo: '안전한 기술 질문' },
		{ ts: '2026-06-17 03:54:34', sensitive: true, action: 'external_api', records: 6, desc: 'Research paper review', descKo: '논문 리뷰' },
		{ ts: '2026-06-17 03:54:41', sensitive: true, action: 'local_api', records: 1, desc: 'Safe question (false positive)', descKo: '안전한 질문 (오탐)' },
		{ ts: '2026-06-17 03:55:16', sensitive: false, action: 'external_api', records: 0, desc: 'Safe technical question', descKo: '안전한 기술 질문' },
		{ ts: '2026-06-17 03:55:21', sensitive: true, action: 'local_api', records: 4, desc: 'Meeting notes with PII', descKo: 'PII 포함 미팅 노트' },
		{ ts: '2026-06-17 03:55:43', sensitive: true, action: 'external_api', records: 2, desc: 'Meeting notes session', descKo: '미팅 노트 세션' },
		{ ts: '2026-06-17 03:56:09', sensitive: false, action: 'external_api', records: 0, desc: 'Safe Rust question', descKo: '안전한 Rust 질문' },
		{ ts: '2026-06-17 03:56:27', sensitive: true, action: 'external_api', records: 6, desc: 'Rust question (false positive)', descKo: 'Rust 질문 (오탐)' },
		{ ts: '2026-06-17 03:56:45', sensitive: true, action: 'external_api', records: 2, desc: 'Meeting notes', descKo: '미팅 노트' },
		{ ts: '2026-06-17 03:56:57', sensitive: false, action: 'external_api', records: 0, desc: 'Safe technical question', descKo: '안전한 기술 질문' },
		{ ts: '2026-06-17 03:57:16', sensitive: true, action: 'local_api', records: 3, desc: 'Business proposal with PII', descKo: 'PII 포함 사업 제안' },
		{ ts: '2026-06-17 03:57:44', sensitive: true, action: 'external_api', records: 2, desc: 'Business proposal session', descKo: '사업 제안 세션' },
		{ ts: '2026-06-17 03:58:07', sensitive: false, action: 'external_api', records: 0, desc: 'Safe Git question', descKo: '안전한 Git 질문' },
		{ ts: '2026-06-17 03:58:14', sensitive: true, action: 'external_api', records: 7, desc: 'Research paper review', descKo: '논문 리뷰' },
		{ ts: '2026-06-17 03:58:31', sensitive: true, action: 'external_api', records: 4, desc: 'Business meeting prep', descKo: '사업 미팅 준비' },
		{ ts: '2026-06-17 03:58:45', sensitive: false, action: 'external_api', records: 0, desc: 'Safe Docker question', descKo: '안전한 Docker 질문' },
		{ ts: '2026-06-17 03:59:06', sensitive: true, action: 'local_api', records: 7, desc: 'Meeting notes with PII', descKo: 'PII 포함 미팅 노트' },
		{ ts: '2026-06-17 03:59:22', sensitive: true, action: 'external_api', records: 5, desc: 'Research paper review', descKo: '논문 리뷰' },
		{ ts: '2026-06-17 03:59:35', sensitive: false, action: 'external_api', records: 0, desc: 'Safe SQL question', descKo: '안전한 SQL 질문' },
		{ ts: '2026-06-17 03:59:54', sensitive: true, action: 'external_api', records: 4, desc: 'Business proposal', descKo: '사업 제안' },
		{ ts: '2026-06-17 04:00:14', sensitive: true, action: 'local_api', records: 3, desc: 'Customer data with PII', descKo: 'PII 포함 고객 데이터' },
		{ ts: '2026-06-17 04:00:30', sensitive: false, action: 'external_api', records: 0, desc: 'Safe React question', descKo: '안전한 React 질문' },
		{ ts: '2026-06-17 04:00:47', sensitive: true, action: 'external_api', records: 5, desc: 'Business report', descKo: '사업 보고서' },
		{ ts: '2026-06-17 04:01:04', sensitive: true, action: 'external_api', records: 3, desc: 'Business meeting prep', descKo: '사업 미팅 준비' },
		{ ts: '2026-06-17 04:01:23', sensitive: false, action: 'external_api', records: 0, desc: 'Safe crypto question', descKo: '안전한 암호화폐 질문' },
		{ ts: '2026-06-17 04:01:41', sensitive: true, action: 'external_api', records: 3, desc: 'Meeting notes', descKo: '미팅 노트' },
		{ ts: '2026-06-17 04:02:00', sensitive: true, action: 'local_api', records: 5, desc: 'Customer loan application', descKo: '고객 대출 신청' },
		{ ts: '2026-06-17 04:02:19', sensitive: false, action: 'external_api', records: 0, desc: 'Safe Docker question', descKo: '안전한 Docker 질문' },
		{ ts: '2026-06-17 04:02:40', sensitive: true, action: 'external_api', records: 3, desc: 'Research idea analysis', descKo: '연구 아이디어 분석' },
		{ ts: '2026-06-17 04:02:59', sensitive: false, action: 'external_api', records: 0, desc: 'Safe SQL question', descKo: '안전한 SQL 질문' },
		{ ts: '2026-06-17 04:03:23', sensitive: true, action: 'external_api', records: 5, desc: 'Research paper analysis', descKo: '논문 분석' },
		{ ts: '2026-06-17 04:03:41', sensitive: true, action: 'external_api', records: 5, desc: 'Business meeting prep', descKo: '사업 미팅 준비' },
		{ ts: '2026-06-17 04:03:59', sensitive: false, action: 'external_api', records: 0, desc: 'Safe Git question', descKo: '안전한 Git 질문' },
		{ ts: '2026-06-17 04:04:20', sensitive: true, action: 'external_api', records: 6, desc: 'Research paper review', descKo: '논문 리뷰' },
		{ ts: '2026-06-17 04:04:40', sensitive: true, action: 'external_api', records: 4, desc: 'Business proposal', descKo: '사업 제안' },
		{ ts: '2026-06-17 04:05:03', sensitive: false, action: 'external_api', records: 0, desc: 'Safe Rust question', descKo: '안전한 Rust 질문' },
		{ ts: '2026-06-17 04:05:22', sensitive: true, action: 'external_api', records: 4, desc: 'Meeting notes with PII', descKo: 'PII 포함 미팅 노트' },
		{ ts: '2026-06-17 04:05:47', sensitive: true, action: 'local_api', records: 6, desc: 'Customer data analysis', descKo: '고객 데이터 분석' },
		{ ts: '2026-06-17 04:06:09', sensitive: false, action: 'external_api', records: 0, desc: 'Safe Docker question', descKo: '안전한 Docker 질문' },
		{ ts: '2026-06-17 04:06:44', sensitive: true, action: 'external_api', records: 3, desc: 'Research analysis', descKo: '연구 분석' },
		{ ts: '2026-06-17 04:07:15', sensitive: false, action: 'external_api', records: 0, desc: 'Safe SQL question', descKo: '안전한 SQL 질문' },
		{ ts: '2026-06-17 04:09:00', sensitive: true, action: 'local_api', records: 6, desc: 'Business meeting with PII', descKo: 'PII 포함 사업 미팅' },
		{ ts: '2026-06-17 04:09:57', sensitive: true, action: 'external_api', records: 8, desc: 'Business analysis', descKo: '사업 분석' },
		{ ts: '2026-06-17 04:10:25', sensitive: false, action: 'external_api', records: 0, desc: 'Safe technical question', descKo: '안전한 기술 질문' },
	];

	const days = [{
		day: 1,
		scenario: 'Hermes Agent — real work session',
		prompts: logEntries.length,
		sensitive: logEntries.filter(e => e.sensitive).length,
		routedLocal: logEntries.filter(e => e.action === 'local_api').length,
		maskedSent: logEntries.filter(e => e.sensitive && e.action === 'external_api').length,
	}];

	const totalPrompts = days.reduce((s, d) => s + d.prompts, 0);
	const totalSensitive = days.reduce((s, d) => s + d.sensitive, 0);
	const totalRoutedLocal = days.reduce((s, d) => s + d.routedLocal, 0);
	const totalMaskedSent = days.reduce((s, d) => s + d.maskedSent, 0);

	let expandedDay = $state<number | null>(null);
	function toggleDay(day: number) {
		expandedDay = expandedDay === day ? null : day;
	}

	let expandedIdx = $state<number | null>(null);

	function toggle(idx: number) {
		expandedIdx = expandedIdx === idx ? null : idx;
	}

	const agentDemos = [
		{ name: 'USAGE_LOG.md', prompts: 46, description: 'Full 46-request session log with per-request details' },
		{ name: 'db-logs.json', prompts: 46, description: 'Raw database export of all usage log entries' },
	];

	const realAgentLogs = [
		{ name: 'USAGE_LOG.md', desc: 'Hermes Agent live session (46 requests, 17 min)' },
	];

	const rawFiles = [
		{ name: 'USAGE_LOG.md', desc: 'Markdown summary with request-level details' },
		{ name: 'db-logs.json', desc: 'JSON export from PostgreSQL usage_logs table' },
	];
</script>

<svelte:head>
	<title>{$t('docs.logs.title')} — Privacy Router</title>
</svelte:head>

<div class="min-h-screen bg-slate-950 text-slate-200">
	<header class="border-b border-slate-800 px-6 py-4">
		<div class="max-w-5xl mx-auto flex items-center justify-between">
			<a href="/documentation" class="text-sm text-slate-400 hover:text-white transition">← {$t('nav.docs')}</a>
			<div class="flex items-center gap-3">
				<span class="text-xs text-slate-500">{$t('docs.logs.title')}</span>
				<LangToggle />
			</div>
		</div>
	</header>

	<main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
		<h1 class="text-3xl font-bold text-white">{$t('docs.logs.title')}</h1>

		<!-- Summary Table -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">{$t('docs.logs.summary')}</h2>
			<div class="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
				<div class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b border-slate-800 bg-slate-900/80">
								<th class="px-4 py-3 text-left text-slate-400 font-medium">{$t('docs.logs.day')}</th>
								<th class="px-4 py-3 text-left text-slate-400 font-medium">{$t('docs.logs.scenario')}</th>
								<th class="px-4 py-3 text-right text-slate-400 font-medium">{$t('docs.logs.prompts')}</th>
								<th class="px-4 py-3 text-right text-slate-400 font-medium">{$t('docs.logs.sensitive')}</th>
								<th class="px-4 py-3 text-right text-slate-400 font-medium">{$t('docs.logs.routed_local')}</th>
								<th class="px-4 py-3 text-right text-slate-400 font-medium">{$t('docs.logs.masked_sent')}</th>
							</tr>
						</thead>
						<tbody class="text-slate-300">
							{#each days as d}
								<tr class="border-b border-slate-800/50 hover:bg-slate-800/30 transition">
									<td class="px-4 py-3 font-medium text-white">{d.day}</td>
									<td class="px-4 py-3">{d.scenario}</td>
									<td class="px-4 py-3 text-right tabular-nums">{d.prompts}</td>
									<td class="px-4 py-3 text-right tabular-nums">
										{#if d.sensitive > 0}
											<span class="text-amber-400">{d.sensitive}</span>
										{:else}
											<span class="text-slate-500">0</span>
										{/if}
									</td>
									<td class="px-4 py-3 text-right tabular-nums">
										{#if d.routedLocal > 0}
											<span class="text-blue-400">{d.routedLocal}</span>
										{:else}
											<span class="text-slate-500">0</span>
										{/if}
									</td>
									<td class="px-4 py-3 text-right tabular-nums">
										{#if d.maskedSent > 0}
											<span class="text-emerald-400">{d.maskedSent}</span>
										{:else}
											<span class="text-slate-500">0</span>
										{/if}
									</td>
								</tr>
							{/each}
							<tr class="bg-slate-900/80 font-medium text-white">
								<td class="px-4 py-3" colspan="2">{$t('docs.logs.total')}</td>
								<td class="px-4 py-3 text-right tabular-nums">{totalPrompts}</td>
								<td class="px-4 py-3 text-right tabular-nums text-amber-400">{totalSensitive}</td>
								<td class="px-4 py-3 text-right tabular-nums text-blue-400">{totalRoutedLocal}</td>
								<td class="px-4 py-3 text-right tabular-nums text-emerald-400">{totalMaskedSent}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
		</section>

		<!-- Day Cards (Accordion) -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">{$t('docs.logs.day')} Details</h2>
			<div class="space-y-3">
				{#each days as d}
					<div class="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
						<button
							class="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-800/30 transition"
							onclick={() => toggleDay(d.day)}
							aria-expanded={expandedDay === d.day}
						>
							<div class="flex items-center gap-4">
								<span class="flex items-center justify-center w-8 h-8 rounded-lg bg-slate-800 text-sm font-bold text-white">
									{d.day}
								</span>
								<div class="text-left">
									<div class="font-medium text-white">{d.scenario}</div>
									<div class="text-xs text-slate-400">{d.prompts} {$t('docs.logs.prompts').toLowerCase()} · {d.sensitive} {$t('docs.logs.sensitive').toLowerCase()}</div>
								</div>
							</div>
							<svg
								class="w-5 h-5 text-slate-400 transition-transform {expandedDay === d.day ? 'rotate-180' : ''}"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
							</svg>
						</button>

						{#if expandedDay === d.day}
							<div class="px-6 pb-5 border-t border-slate-800/50 pt-4 space-y-4">
								<!-- Description -->
								<div>
									<h4 class="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">{$t('docs.logs.description')}</h4>
									<p class="text-sm text-slate-300">{d.description}</p>
									<p class="text-xs text-slate-500 mt-0.5">{d.descriptionEn}</p>
								</div>

								<!-- Judgment Summary -->
								<div>
									<h4 class="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">{$t('docs.logs.judgment')}</h4>
									<div class="rounded-lg bg-slate-800/50 p-4 space-y-2">
										<div class="flex items-center gap-2">
											<span class="text-xs text-slate-400">{$t('docs.logs.is_sensitive')}:</span>
											{#if d.judgment.is_sensitive}
												<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-amber-500/20 text-amber-400">True</span>
											{:else}
												<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-emerald-500/20 text-emerald-400">False</span>
											{/if}
										</div>
										<div class="flex items-center gap-2">
											<span class="text-xs text-slate-400">{$t('docs.logs.records')}:</span>
											<span class="text-sm text-white font-mono">{d.judgment.records}</span>
										</div>
										<div class="flex items-center gap-2">
											<span class="text-xs text-slate-400">{$t('docs.logs.policy_action')}:</span>
											<span class="text-sm text-blue-400 font-mono">{d.judgment.policy_action}</span>
										</div>
									</div>
								</div>

								<!-- Raw Log Link -->
								<div>
									<a
										href="/usage-log/{d.logFile}"
										target="_blank"
										class="inline-flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition"
									>
										<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
										</svg>
										{$t('docs.logs.raw_log')} →
									</a>
								</div>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</section>

		<!-- Agent Demo Logs -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">{$t('docs.logs.agent_demo')}</h2>
			<div class="grid gap-4 sm:grid-cols-2">
				{#each agentDemos as demo}
					<div class="rounded-xl border border-slate-800 bg-slate-900/50 p-6 space-y-3">
						<div class="flex items-center gap-3">
							<span class="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-500/10 text-blue-400">
								<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
								</svg>
							</span>
							<div>
								<div class="font-medium text-white font-mono text-sm">{demo.name}</div>
								<div class="text-xs text-slate-400">{demo.prompts} prompts</div>
							</div>
						</div>
						<p class="text-sm text-slate-400">{demo.description}</p>
						<a
							href="/usage-log/{demo.name}"
							target="_blank"
							class="inline-flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition"
						>
							{$t('docs.logs.raw_log')} →
						</a>
					</div>
				{/each}
			</div>
		</section>

		<!-- Real Agent Logs -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">실제 에이전트 작업 로그</h2>
			<p class="text-sm text-slate-400">Hermes Agent로 실제 작업을 수행하면서 Privacy Router가 어떻게 개입했는지 기록한 로그입니다.</p>
			<div class="grid gap-4 sm:grid-cols-2">
				{#each realAgentLogs as log}
					<div class="rounded-xl border border-slate-800 bg-slate-900/50 p-6 space-y-3">
						<div class="flex items-center gap-3">
							<span class="flex items-center justify-center w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-400">
								<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
								</svg>
							</span>
							<div>
								<div class="font-medium text-white font-mono text-sm">{log.desc}</div>
							</div>
						</div>
						<a
							href="/usage-log/{log.name}"
							target="_blank"
							class="inline-flex items-center gap-2 text-sm text-emerald-400 hover:text-emerald-300 transition"
						>
							{$t('docs.logs.raw_log')} →
						</a>
					</div>
				{/each}
			</div>
		</section>

		<!-- Raw Log Files -->
		<section class="space-y-4">
			<h2 class="text-xl font-semibold text-white">{$t('docs.logs.raw_files')}</h2>
			<div class="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
				<div class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b border-slate-800 bg-slate-900/80">
								<th class="px-4 py-3 text-left text-slate-400 font-medium">{$t('docs.logs.filename')}</th>
								<th class="px-4 py-3 text-left text-slate-400 font-medium">{$t('docs.logs.description')}</th>
								<th class="px-4 py-3 text-right text-slate-400 font-medium"></th>
							</tr>
						</thead>
						<tbody class="text-slate-300">
							{#each rawFiles as file}
								<tr class="border-b border-slate-800/50 hover:bg-slate-800/30 transition">
									<td class="px-4 py-3 font-mono text-xs text-blue-400">{file.name}</td>
									<td class="px-4 py-3 text-slate-400">{file.desc}</td>
									<td class="px-4 py-3 text-right">
										<a
											href="/usage-log/{file.name}"
											target="_blank"
											class="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition"
										>
											<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
											</svg>
											{$t('docs.logs.download')}
										</a>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		</section>
	</main>
</div>
