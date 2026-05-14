<script lang="ts">
	import { onMount } from 'svelte';
	import { geoEqualEarth, geoPath, type GeoPath } from 'd3-geo';
	import { feature } from 'topojson-client';
	import type { Movement } from '$lib/types';

	let { movements }: { movements: Movement[] } = $props();

	const W = 960;
	const H = 480;
	const projection = geoEqualEarth()
		.scale(180)
		.translate([W / 2, H / 2]);
	const path: GeoPath = geoPath(projection);

	let countriesPath = $state<string>('');
	let hoveredSlug = $state<string | null>(null);

	// Refined region palette — slightly desaturated, more cohesive
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

	onMount(async () => {
		try {
			const res = await fetch('/world-110m.json');
			const topo = await res.json();
			const countries = feature(topo, topo.objects.countries) as any;
			countriesPath = path(countries) ?? '';
		} catch (e) {
			console.error('Failed to load world map:', e);
		}
	});

	// Project each movement and cluster co-located dots into a spider ring.
	// Movements whose projected positions are within `CLUSTER_RADIUS` pixels of
	// each other (e.g. half a dozen French movements in Paris) are spaced out
	// around a small circle around their group centroid, so all dots remain
	// individually hoverable and clickable.
	const CLUSTER_RADIUS = 14;
	const SPIDER_RADIUS = 9;

	type Dot = {
		m: Movement;
		x: number; // display position (after spidering)
		y: number;
		anchorX: number; // group anchor (original projected centroid)
		anchorY: number;
		color: string;
		groupSize: number;
	};

	const dots = $derived.by((): Dot[] => {
		const projected = movements
			.map((m) => {
				const p = projection(m.coords);
				if (!p) return null;
				return { m, px: p[0], py: p[1] };
			})
			.filter((d): d is { m: Movement; px: number; py: number } => d !== null);

		// Greedy cluster by proximity
		const groups: { cx: number; cy: number; items: typeof projected }[] = [];
		for (const p of projected) {
			let placed = false;
			for (const g of groups) {
				const dx = p.px - g.cx;
				const dy = p.py - g.cy;
				if (dx * dx + dy * dy < CLUSTER_RADIUS * CLUSTER_RADIUS) {
					g.items.push(p);
					// Update centroid incrementally
					g.cx = g.items.reduce((s, it) => s + it.px, 0) / g.items.length;
					g.cy = g.items.reduce((s, it) => s + it.py, 0) / g.items.length;
					placed = true;
					break;
				}
			}
			if (!placed) groups.push({ cx: p.px, cy: p.py, items: [p] });
		}

		const out: Dot[] = [];
		for (const g of groups) {
			if (g.items.length === 1) {
				const p = g.items[0];
				out.push({
					m: p.m,
					x: p.px,
					y: p.py,
					anchorX: p.px,
					anchorY: p.py,
					color: regionColors[p.m.region] ?? '#888',
					groupSize: 1
				});
			} else {
				// Spider out around centroid. Sort by period start so order is meaningful.
				const sorted = [...g.items].sort((a, b) => a.m.period.start - b.m.period.start);
				const n = sorted.length;
				const radius = SPIDER_RADIUS + (n > 4 ? (n - 4) * 1.5 : 0);
				for (let i = 0; i < n; i++) {
					const angle = (i / n) * Math.PI * 2 - Math.PI / 2; // start at top
					const x = g.cx + radius * Math.cos(angle);
					const y = g.cy + radius * Math.sin(angle);
					out.push({
						m: sorted[i].m,
						x,
						y,
						anchorX: g.cx,
						anchorY: g.cy,
						color: regionColors[sorted[i].m.region] ?? '#888',
						groupSize: n
					});
				}
			}
		}
		return out;
	});

	const hovered = $derived(
		hoveredSlug ? movements.find((m) => m.slug === hoveredSlug) ?? null : null
	);

	function shortSummary(s: string | undefined, max = 220): string {
		if (!s) return '';
		const cleaned = s.replace(/\s+/g, ' ').trim();
		if (cleaned.length <= max) return cleaned;
		return cleaned.slice(0, max).replace(/\s+\S*$/, '') + '…';
	}
</script>

<div class="map-wrap">
	<svg
		viewBox="0 0 {W} {H}"
		preserveAspectRatio="xMidYMid meet"
		role="img"
		aria-label="World map of film movements"
	>
		<defs>
			<filter id="dot-shadow" x="-50%" y="-50%" width="200%" height="200%">
				<feGaussianBlur in="SourceAlpha" stdDeviation="1.2" />
				<feOffset dx="0" dy="0.6" result="offsetblur" />
				<feComponentTransfer>
					<feFuncA type="linear" slope="0.55" />
				</feComponentTransfer>
				<feMerge>
					<feMergeNode />
					<feMergeNode in="SourceGraphic" />
				</feMerge>
			</filter>
		</defs>

		<rect x="0" y="0" width={W} height={H} fill="var(--bg-2)" />
		{#if countriesPath}
			<path
				d={countriesPath}
				fill="var(--bg-3, #2a2a2a)"
				stroke="var(--border)"
				stroke-width="0.4"
			/>
		{/if}

		<!-- Spider leader lines for clustered groups -->
		<g class="leaders">
			{#each dots as d (d.m.slug)}
				{#if d.groupSize > 1}
					<line
						x1={d.anchorX}
						y1={d.anchorY}
						x2={d.x}
						y2={d.y}
						stroke="var(--border)"
						stroke-width="0.5"
						opacity="0.6"
					/>
				{/if}
			{/each}
		</g>

		<g class="dots">
			{#each dots as d (d.m.slug)}
				<a href="/movement/{d.m.slug}" aria-label={d.m.name}>
					<circle
						cx={d.x}
						cy={d.y}
						r={hoveredSlug === d.m.slug ? 7 : 4.8}
						fill={d.color}
						stroke="#0008"
						stroke-width="0.6"
						filter="url(#dot-shadow)"
						opacity={hoveredSlug && hoveredSlug !== d.m.slug ? 0.3 : 0.95}
						onmouseenter={() => (hoveredSlug = d.m.slug)}
						onmouseleave={() => (hoveredSlug = null)}
						onfocus={() => (hoveredSlug = d.m.slug)}
						onblur={() => (hoveredSlug = null)}
					>
						<title>
							{d.m.name} ({d.m.period.start}{d.m.period.end ? `–${d.m.period.end}` : '–'}) · {d.m.country}
						</title>
					</circle>
				</a>
			{/each}
		</g>
	</svg>

	<div class="readout" class:visible={!!hovered}>
		{#if hovered}
			<div class="readout-head">
				<strong>{hovered.name}</strong>
				<span class="dim">
					{hovered.period.start}{hovered.period.end ? `–${hovered.period.end}` : '–'} · {hovered.country}
				</span>
			</div>
			<p class="readout-summary">{shortSummary(hovered.summary)}</p>
		{:else}
			<span class="dim">Hover a dot to see a movement. Click to open its page.</span>
		{/if}
	</div>

	<div class="legend">
		{#each Object.entries(regionColors) as [region, color] (region)}
			<span class="legend-item">
				<span class="swatch" style="background: {color}"></span>
				{region}
			</span>
		{/each}
	</div>
</div>

<style>
	.map-wrap {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-bottom: 2rem;
	}
	svg {
		display: block;
		width: 100%;
		height: auto;
		background: var(--bg-2);
		border: 1px solid var(--border);
		border-radius: 4px;
	}
	.dots a {
		cursor: pointer;
		outline: none;
	}
	.dots circle {
		transition:
			r 120ms ease,
			opacity 120ms ease;
	}
	.leaders line {
		pointer-events: none;
	}
	.readout {
		min-height: 4rem;
		font-size: 0.9rem;
		color: var(--fg);
		padding: 0.5rem 0.75rem;
		background: var(--bg-2);
		border: 1px solid var(--border);
		border-radius: 4px;
	}
	.readout-head {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		align-items: baseline;
	}
	.readout-summary {
		margin: 0.4rem 0 0;
		font-family: var(--font-serif);
		font-size: 0.9rem;
		line-height: 1.55;
		color: var(--fg-dim);
		max-width: 720px;
	}
	.readout .dim {
		color: var(--fg-dim);
	}
	.legend {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem 1rem;
		font-size: 0.8rem;
		color: var(--fg-dim);
		padding-top: 0.25rem;
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
