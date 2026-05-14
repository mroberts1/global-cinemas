<script lang="ts">
	import { movements } from '$lib/movements';
</script>

<svelte:head>
	<title>Influences — Global Cinemas</title>
</svelte:head>

<h1>Influence Graph</h1>
<p class="dim">
	A directed graph of cross-movement influence — Italian Neorealism feeds the French New Wave feeds
	Cinema Novo feeds the Iranian New Wave.
</p>

<p class="dim">
	<em>Force-directed visualization coming soon.</em> For now, here are all influence edges encoded
	in the data:
</p>

{#each movements as m}
	{#if m.influences_to?.length}
		<p>
			<a href="/movement/{m.slug}"><strong>{m.name}</strong></a>
			→
			{#each m.influences_to as t, i}
				<a href="/movement/{t}">{t}</a>{i < m.influences_to.length - 1 ? ', ' : ''}
			{/each}
		</p>
	{/if}
{/each}
