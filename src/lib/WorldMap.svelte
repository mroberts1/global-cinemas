<script lang="ts">
	import { onMount } from 'svelte';
	import { geoNaturalEarth1, geoPath, type GeoPath } from 'd3-geo';
	import { feature } from 'topojson-client';
	import type { Movement } from '$lib/types';

	let { movements }: { movements: Movement[] } = $props();

	const W = 960;
	const H = 480;
	const projection = geoNaturalEarth1()
		.scale(180)
		.translate([W / 2, H / 2]);
	const path: GeoPath = geoPath(projection);

	let countriesPath = $state<string>('');
	let graticulePath = $state<string>('');
	let hoveredSlug = $state<string | null>(null);

	// Color palette per region (theme-aware via CSS vars, but we use named accents here)
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

	// Project each movement's coordinates to SVG x/y
	const dots = $derived(
		movements
			.map((m) => {
				const projected = projection(m.coords);
				if (!projected) return null;
				return {
					m,
					x: projected[0],
					y: projected[1],
					color: regionColors[m.region] ?? '#888'
				};
			})
			.filter((d): d is { m: Movement; x: number; y: number; color: string } => d !== null)
	);

	// Stable hover info
	const hovered = $derived(hoveredSlug ? movements.find((m) => m.slug === hoveredSlug) ?? null : null);
</script>

<div class="map-wrap">
	<svg
		viewBox="0 0 {W} {H}"
		preserveAspectRatio="xMidYMid meet"
		role="img"
		aria-label="World map of film movements"
	>
		<rect x="0" y="0" width={W} height={H} fill="var(--bg-2)" />
		{#if countriesPath}
			<path d={countriesPath} fill="var(--bg-3, #2a2a2a)" stroke="var(--border)" stroke-width="0.4" />
		{/if}
		<g class="dots">
			{#each dots as d (d.m.slug)}
				<a href="/movement/{d.m.slug}" aria-label={d.m.name}>
					<circle
						cx={d.x}
						cy={d.y}
						r={hoveredSlug === d.m.slug ? 7 : 4.5}
						fill={d.color}
						stroke="#000"
						stroke-width="0.6"
						opacity={hoveredSlug && hoveredSlug !== d.m.slug ? 0.35 : 0.92}
						onmouseenter={() => (hoveredSlug = d.m.slug)}
						onmouseleave={() => (hoveredSlug = null)}
						onfocus={() => (hoveredSlug = d.m.slug)}
						onblur={() => (hoveredSlug = null)}
					>
						<title>{d.m.name} ({d.m.period.start}{d.m.period.end ? `–${d.m.period.end}` : '–'}) · {d.m.country}</title>
					</circle>
				</a>
			{/each}
		</g>
	</svg>

	<div class="readout" class:visible={!!hovered}>
		{#if hovered}
			<strong>{hovered.name}</strong>
			<span class="dim">
				{hovered.period.start}{hovered.period.end ? `–${hovered.period.end}` : '–'} · {hovered.country}
			</span>
		{:else}
			<span class="dim">Hover a dot to see a movement.</span>
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
	.readout {
		min-height: 1.5rem;
		font-size: 0.9rem;
		color: var(--fg);
		padding: 0.25rem 0;
	}
	.readout .dim {
		color: var(--fg-dim);
		margin-left: 0.5rem;
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
