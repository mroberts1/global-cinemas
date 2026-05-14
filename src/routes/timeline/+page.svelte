<script lang="ts">
	import { movements } from '$lib/movements';
</script>

<svelte:head>
	<title>Timeline — Global Cinemas</title>
</svelte:head>

<h1>Timeline</h1>
<p class="dim">A horizontal river of film movements from 1895 to today.</p>

<section class="rows">
	{#each movements as m}
		<a class="row" href="/movement/{m.slug}">
			<span class="years">
				{m.period.start}{m.period.end ? `–${m.period.end}` : '–'}
			</span>
			<span class="name">{m.name}</span>
			<span class="country dim">{m.country}</span>
		</a>
	{/each}
</section>

<style>
	.rows {
		display: flex;
		flex-direction: column;
		gap: 0;
	}
	.row {
		display: grid;
		grid-template-columns: 110px 1fr 200px;
		gap: 1rem;
		padding: 0.5rem 0.75rem;
		border-bottom: 1px solid var(--border);
		color: var(--fg);
	}
	.row:hover {
		background: var(--bg-2);
		border-bottom-color: var(--accent);
	}
	.years {
		font-family: var(--font-mono);
		font-size: 0.85rem;
		color: var(--fg-dim);
	}
	.name {
		font-family: var(--font-serif);
	}
</style>
