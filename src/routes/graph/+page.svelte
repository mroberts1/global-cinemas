<script lang="ts">
	import { movements } from '$lib/movements';
	import {
		forceSimulation,
		forceLink,
		forceManyBody,
		forceCenter,
		forceCollide,
		type SimulationNodeDatum,
		type SimulationLinkDatum
	} from 'd3-force';
	import { onMount, onDestroy } from 'svelte';

	type Node = SimulationNodeDatum & {
		slug: string;
		name: string;
		region: string;
		periodStart: number;
		color: string;
	};
	type Link = SimulationLinkDatum<Node> & { source: string | Node; target: string | Node };

	const regionColors: Record<string, string> = {
		Europe: '#e07a5f',
		'East Asia': '#f2cc8f',
		'South Asia': '#f7b267',
		'Southeast Asia': '#f4a261',
		'Middle East': '#e9c46a',
		Africa: '#8ab17d',
		'North America': '#81b29a',
		'Latin America': '#a78bfa',
		Oceania: '#56cfe1'
	};

	const W = 960;
	const H = 640;

	// Build nodes and links
	const nodes: Node[] = movements.map((m) => ({
		slug: m.slug,
		name: m.name,
		region: m.region,
		periodStart: m.period.start,
		color: regionColors[m.region] ?? '#888'
	}));

	const slugSet = new Set(nodes.map((n) => n.slug));
	const links: Link[] = [];
	for (const m of movements) {
		for (const target of m.influences_to ?? []) {
			if (slugSet.has(target)) {
				links.push({ source: m.slug, target });
			}
		}
	}

	let simNodes = $state<Node[]>([]);
	let simLinks = $state<{ source: Node; target: Node }[]>([]);
	let hoveredSlug = $state<string | null>(null);

	let simulation: ReturnType<typeof forceSimulation<Node>> | null = null;

	onMount(() => {
		// Deep-clone nodes/links so we can re-init simulation idempotently
		const ns: Node[] = nodes.map((n) => ({ ...n }));
		const ls: Link[] = links.map((l) => ({ source: l.source, target: l.target }));

		simulation = forceSimulation<Node>(ns)
			.force(
				'link',
				forceLink<Node, Link>(ls)
					.id((d) => d.slug)
					.distance(80)
					.strength(0.6)
			)
			.force('charge', forceManyBody().strength(-180))
			.force('center', forceCenter(W / 2, H / 2))
			.force('collide', forceCollide(18))
			.alpha(1)
			.alphaDecay(0.025);

		simulation.on('tick', () => {
			simNodes = ns.map((n) => ({ ...n }));
			simLinks = ls.map((l) => ({
				source: l.source as Node,
				target: l.target as Node
			}));
		});
	});

	onDestroy(() => {
		simulation?.stop();
	});

	// Edge highlighting on hover: an edge is "active" if either endpoint is hovered
	function isEdgeActive(l: { source: Node; target: Node }): boolean {
		if (!hoveredSlug) return false;
		return l.source.slug === hoveredSlug || l.target.slug === hoveredSlug;
	}

	function isNodeNeighbor(slug: string): boolean {
		if (!hoveredSlug) return false;
		if (slug === hoveredSlug) return true;
		return simLinks.some(
			(l) =>
				(l.source.slug === hoveredSlug && l.target.slug === slug) ||
				(l.target.slug === hoveredSlug && l.source.slug === slug)
		);
	}
</script>

<svelte:head>
	<title>Influences — Global Cinemas</title>
</svelte:head>

<h1>Influence Graph</h1>
<p class="lead dim">
	A directed network of cross-movement influence. Italian Neorealism feeds the French New Wave,
	which feeds Cinema Novo, which feeds Iranian New Wave… {simLinks.length} edges across {simNodes.length}
	movements. Drag — well, hover — and click any node to open its page.
</p>

<div class="graph-wrap">
	<svg
		viewBox="0 0 {W} {H}"
		preserveAspectRatio="xMidYMid meet"
		role="img"
		aria-label="Influence graph of film movements"
	>
		<defs>
			<marker
				id="arrow"
				viewBox="0 -5 10 10"
				refX="14"
				refY="0"
				markerWidth="6"
				markerHeight="6"
				orient="auto"
			>
				<path d="M0,-5L10,0L0,5" fill="var(--fg-dim)" />
			</marker>
			<marker
				id="arrow-active"
				viewBox="0 -5 10 10"
				refX="14"
				refY="0"
				markerWidth="7"
				markerHeight="7"
				orient="auto"
			>
				<path d="M0,-5L10,0L0,5" fill="var(--accent, #e07a5f)" />
			</marker>
		</defs>

		<g class="edges">
			{#each simLinks as l, i (i)}
				{@const active = isEdgeActive(l)}
				<line
					x1={l.source.x ?? 0}
					y1={l.source.y ?? 0}
					x2={l.target.x ?? 0}
					y2={l.target.y ?? 0}
					stroke={active ? 'var(--accent, #e07a5f)' : 'var(--fg-dim)'}
					stroke-width={active ? 1.6 : 0.8}
					opacity={hoveredSlug && !active ? 0.1 : 0.5}
					marker-end={active ? 'url(#arrow-active)' : 'url(#arrow)'}
				/>
			{/each}
		</g>

		<g class="nodes">
			{#each simNodes as n (n.slug)}
				{@const neighbor = isNodeNeighbor(n.slug)}
				<a href="/movement/{n.slug}" aria-label={n.name}>
					<circle
						cx={n.x ?? 0}
						cy={n.y ?? 0}
						r={hoveredSlug === n.slug ? 11 : 7}
						fill={n.color}
						stroke="#0008"
						stroke-width="0.8"
						opacity={hoveredSlug && !neighbor ? 0.25 : 0.95}
						onmouseenter={() => (hoveredSlug = n.slug)}
						onmouseleave={() => (hoveredSlug = null)}
						onfocus={() => (hoveredSlug = n.slug)}
						onblur={() => (hoveredSlug = null)}
					>
						<title>{n.name} ({n.periodStart}) · {n.region}</title>
					</circle>
					<text
						x={(n.x ?? 0) + 11}
						y={(n.y ?? 0) + 4}
						font-size="10"
						fill="var(--fg)"
						opacity={hoveredSlug ? (neighbor ? 1 : 0.15) : 0.85}
						pointer-events="none"
					>
						{n.name}
					</text>
				</a>
			{/each}
		</g>
	</svg>
</div>

<div class="legend">
	{#each Object.entries(regionColors) as [region, color] (region)}
		<span class="legend-item">
			<span class="swatch" style="background: {color}"></span>
			{region}
		</span>
	{/each}
</div>

<style>
	h1 {
		margin-bottom: 0.5rem;
	}
	.lead {
		max-width: 720px;
		font-size: 0.95rem;
		line-height: 1.6;
		margin-bottom: 1.5rem;
	}
	.graph-wrap {
		border: 1px solid var(--border);
		background: var(--bg-2);
		border-radius: 4px;
		overflow: hidden;
	}
	svg {
		display: block;
		width: 100%;
		height: auto;
	}
	.nodes a {
		cursor: pointer;
		outline: none;
	}
	.nodes circle {
		transition:
			r 120ms ease,
			opacity 120ms ease;
	}
	.nodes text {
		font-family: var(--font-sans, system-ui, sans-serif);
		user-select: none;
		transition: opacity 120ms ease;
	}
	.edges line {
		transition:
			opacity 120ms ease,
			stroke 120ms ease,
			stroke-width 120ms ease;
	}
	.legend {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem 1rem;
		font-size: 0.8rem;
		color: var(--fg-dim);
		margin-top: 0.75rem;
	}
	.legend-item {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
	}
	.swatch {
		display: inline-block;
		width: 0.7rem;
		height: 0.7rem;
		border-radius: 50%;
		border: 1px solid #0008;
	}
</style>
