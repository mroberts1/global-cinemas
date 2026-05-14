<script lang="ts">
	import { page } from '$app/state';
	import { movementsBySlug } from '$lib/movements';

	let movement = $derived(movementsBySlug[page.params.slug]);
</script>

<svelte:head>
	<title>{movement ? movement.name : 'Not found'} — Global Cinemas</title>
	<meta
		name="description"
		content={movement?.summary || `${movement?.name || page.params.slug} film movement`}
	/>
</svelte:head>

{#if !movement}
	<h1>Not found</h1>
	<p>No movement with slug <code>{page.params.slug}</code>.</p>
{:else}
	<article>
		<header class="hdr">
			<h1>{movement.name}</h1>
			<p class="meta dim">
				{movement.period.start ?? '?'}{movement.period.end ? `–${movement.period.end}` : '–'} ·
				{movement.country || '—'}{movement.region ? ` · ${movement.region}` : ''}
			</p>
		</header>

		{#if movement.summary}
			<p class="summary">{movement.summary}</p>
		{/if}
		{#if movement.long_description && movement.long_description !== movement.summary}
			<div class="prose">{movement.long_description}</div>
		{/if}

		{#if movement.key_directors?.length}
			<section>
				<h2>Key directors</h2>
				<ul class="inline">
					{#each movement.key_directors as d}
						<li>{d}</li>
					{/each}
				</ul>
			</section>
		{/if}

		{#if movement.canonical_films?.length}
			<section>
				<h2>Canonical films</h2>
				<ol class="films">
					{#each movement.canonical_films as f}
						<li>
							{#if f.letterboxd_url}
								<a href={f.letterboxd_url} target="_blank" rel="noreferrer">{f.title}</a>
							{:else}
								{f.title}
							{/if}
							{#if f.year}<span class="dim"> ({f.year})</span>{/if}
							{#if f.director}<span class="dim"> — {f.director}</span>{/if}
						</li>
					{/each}
				</ol>
			</section>
		{/if}

		{#if movement.influences_from?.length || movement.influences_to?.length}
			<section class="influences">
				{#if movement.influences_from?.length}
					<div>
						<h2>Influenced by</h2>
						<ul class="inline">
							{#each movement.influences_from as slug}
								{@const m = movementsBySlug[slug]}
								{#if m}
									<li><a href="/movement/{slug}">{m.name}</a></li>
								{:else}
									<li class="dim">{slug}</li>
								{/if}
							{/each}
						</ul>
					</div>
				{/if}
				{#if movement.influences_to?.length}
					<div>
						<h2>Influenced</h2>
						<ul class="inline">
							{#each movement.influences_to as slug}
								{@const m = movementsBySlug[slug]}
								{#if m}
									<li><a href="/movement/{slug}">{m.name}</a></li>
								{:else}
									<li class="dim">{slug}</li>
								{/if}
							{/each}
						</ul>
					</div>
				{/if}
			</section>
		{/if}

		<footer class="src dim">
			{#if movement.cinema_waves_url}
				<a href={movement.cinema_waves_url} target="_blank" rel="noreferrer">Cinema Waves entry</a>
			{/if}
		</footer>
	</article>
{/if}

<style>
	article {
		max-width: 760px;
	}
	.hdr {
		padding: 0;
		border: none;
		background: none;
		display: block;
		position: static;
	}
	.meta {
		font-style: italic;
	}
	.summary {
		font-family: var(--font-serif);
		font-size: 1.1rem;
		line-height: 1.65;
		margin: 1.5rem 0;
		padding-left: 1rem;
		border-left: 3px solid var(--accent);
	}
	.prose {
		white-space: pre-wrap;
		line-height: 1.7;
	}
	ul.inline {
		list-style: none;
		padding: 0;
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem 1rem;
	}
	ol.films {
		padding-left: 1.5rem;
	}
	ol.films li {
		margin: 0.25rem 0;
	}
	.influences {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		margin-top: 2rem;
	}
	.src {
		margin-top: 3rem;
		padding-top: 1rem;
		border-top: 1px solid var(--border);
		font-size: 0.85rem;
	}
</style>
