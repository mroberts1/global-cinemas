<script lang="ts">
	import { movements } from '$lib/movements';
	import WorldMap from '$lib/WorldMap.svelte';
</script>

<svelte:head>
	<title>Global Cinemas — an atlas of film movements</title>
	<meta
		name="description"
		content="A visual atlas of global film movements, from the Cinema of Attractions to today's New Extremity. Trace influence across countries, decades, and waves."
	/>
</svelte:head>

<section class="hero">
	<h1>An Atlas of Film Movements</h1>
	<p class="lead">
		From the <em>Cinema of Attractions</em> in 1895 to <em>New Extremity</em> today, cinema has
		moved in waves: ruptures, manifestos, and revivals that reshape what film can be.
		<strong>Global Cinemas</strong> is a map of those movements — where they began, who they answered,
		and what they made possible.
	</p>
</section>

<WorldMap {movements} />

{#if movements.length === 0}
	<section class="empty">
		<h2>No movements loaded yet.</h2>
		<p class="dim">
			Run the scrapers in <code>scrapers/</code> to populate <code>src/lib/data/movements/</code>.
		</p>
	</section>
{:else}
	<section>
		<h2 class="grid-h">All {movements.length} movements</h2>
		<div class="grid">
			{#each movements as m (m.slug)}
				<a class="card" href="/movement/{m.slug}">
					<header>
						<h3>{m.name}</h3>
						<small class="dim">
							{m.period.start}{m.period.end ? `–${m.period.end}` : '–'} · {m.country}
						</small>
					</header>
					<p class="summary">{m.summary || ''}</p>
					{#if m.canonical_films?.length}
						<small class="films dim">{m.canonical_films.length} canonical films</small>
					{/if}
				</a>
			{/each}
		</div>
	</section>
{/if}

<style>
	.hero {
		padding: 1.5rem 0 1.5rem;
		max-width: 720px;
	}
	.lead {
		font-family: var(--font-serif);
		font-size: 1.15rem;
		line-height: 1.65;
		color: var(--fg);
	}
	.grid-h {
		font-size: 1rem;
		font-weight: 500;
		color: var(--fg-dim);
		margin: 1rem 0 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	.empty {
		text-align: center;
		padding: 3rem 0;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1rem;
	}
	.card {
		display: block;
		padding: 1rem;
		border: 1px solid var(--border);
		border-radius: 4px;
		background: var(--bg-2);
		color: var(--fg);
	}
	.card:hover {
		border-color: var(--accent);
	}
	.card header {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		margin-bottom: 0.5rem;
		padding: 0;
		border: none;
		background: none;
		position: static;
	}
	.card h3 {
		margin: 0;
		font-size: 1.05rem;
	}
	.summary {
		font-size: 0.9rem;
		color: var(--fg-dim);
		margin: 0.25rem 0;
	}
</style>
