import { movementSlugs } from '$lib/movements';

export const prerender = true;

export function entries() {
	return movementSlugs.map((slug) => ({ slug }));
}
