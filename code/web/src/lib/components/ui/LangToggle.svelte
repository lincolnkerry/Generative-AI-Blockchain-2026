<script lang="ts">
	import { locale, toggleLocale } from '$lib/i18n';
</script>

<button
	onclick={toggleLocale}
	class="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700 hover:text-white transition cursor-pointer"
>
	{$locale === 'en' ? '🇰🇷 한국어' : '🇺🇸 English'}
</button>
