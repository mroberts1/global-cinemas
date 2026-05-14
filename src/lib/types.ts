// Type definitions for global-cinemas

export interface Film {
	title: string;
	year?: string;
	director?: string;
	letterboxd_url?: string;
	tmdb_id?: string;
	rating?: number;
	source_count?: number; // appearances in movement source lists
}

export interface Movement {
	slug: string;
	name: string;
	period: { start: number; end?: number }; // years
	country: string; // primary country
	countries: string[]; // all participating countries
	region: string; // continent / region rollup
	coords: [number, number]; // [longitude, latitude] for map placement
	summary: string; // short prose description
	long_description?: string; // longer essay text from CinemaWaves
	key_directors: string[];
	canonical_films: Film[];
	influences_from: string[]; // upstream movement slugs
	influences_to: string[]; // downstream movement slugs
	source_lists?: string[]; // letterboxd lists used
	wikipedia_url?: string;
	cinema_waves_url?: string;
}

export type Region =
	| 'Europe'
	| 'East Asia'
	| 'South Asia'
	| 'Southeast Asia'
	| 'Middle East'
	| 'Africa'
	| 'North America'
	| 'Latin America'
	| 'Oceania';
