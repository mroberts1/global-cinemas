<script lang="ts">
	import { movements, regions } from '$lib/movements';

	const grouped = $derived(
		regions
			.map((region) => ({
				region,
				movements: movements.filter((m) => m.region === region)
			}))
			.filter((g) => g.movements.length > 0)
	);
</script>

<svelte:head>
	<title>Regions — Global Cinemas</title>
</svelte:head>

<h1>Regions</h1>
<p class="dim">Movements grouped by region of origin.</p>

{#each grouped as g}
	<section>
		<h2>{g.region}</h2>
		<ul class="region-list">
			{#each g.movements as m}
				<li>
					<a href="/movement/{m.slug}">{m.name}</a>
					<span class="dim"> · {m.country} · {m.period.start}{m.period.end ? `–${m.period.end}` : '–'}</span>
				</li>
			{/each}
		</ul>
	</section>
{/each}

<style>
	.region-list {
		list-style: none;
		padding: 0;
	}
	.region-list li {
		padding: 0.4rem 0;
		border-bottom: 1px dotted var(--border);
	}
</style>
