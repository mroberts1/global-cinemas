import type { Movement } from './types';

// Auto-discover all movement JSONs at build time.
const modules = import.meta.glob('./data/movements/*.json', { eager: true }) as Record<
	string,
	{ default: Movement }
>;

export const movements: Movement[] = Object.values(modules)
	.map((m) => m.default)
	.sort((a, b) => a.period.start - b.period.start);

export const movementsBySlug: Record<string, Movement> = Object.fromEntries(
	movements.map((m) => [m.slug, m])
);

export const movementSlugs: string[] = movements.map((m) => m.slug);

export const regions = [
	'Europe',
	'East Asia',
	'South Asia',
	'Southeast Asia',
	'Middle East',
	'Africa',
	'North America',
	'Latin America',
	'Oceania'
] as const;
