import { getCollection, type CollectionEntry } from 'astro:content';

export type NewsEntry = CollectionEntry<'news'>;

export const CONTINENT_ORDER = [
	'Africa',
	'Asia',
	'Europe',
	'North America',
	'South America',
	'Oceania',
] as const;

export async function getPublishedNews(): Promise<NewsEntry[]> {
	const entries = await getCollection('news', ({ data }) => !data.draft);
	return entries.sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
}

export function formatDate(date: Date, locale = 'en'): string {
	return date.toLocaleDateString(locale, {
		year: 'numeric',
		month: 'long',
		day: 'numeric',
	});
}

export function dateKey(date: Date): string {
	return date.toISOString().slice(0, 10);
}

export type CountryGroup = {
	country: string;
	items: NewsEntry[];
};

export type ContinentGroup = {
	continent: string;
	countries: CountryGroup[];
};

/** Group news by continent, then by country. */
export function groupByRegion(entries: NewsEntry[]): ContinentGroup[] {
	const byContinent = new Map<string, Map<string, NewsEntry[]>>();

	for (const entry of entries) {
		const { continent, country } = entry.data;
		if (!byContinent.has(continent)) {
			byContinent.set(continent, new Map());
		}
		const countries = byContinent.get(continent)!;
		if (!countries.has(country)) {
			countries.set(country, []);
		}
		countries.get(country)!.push(entry);
	}

	return CONTINENT_ORDER.filter((c) => byContinent.has(c)).map((continent) => {
		const countries = byContinent.get(continent)!;
		return {
			continent,
			countries: [...countries.entries()]
				.sort(([a], [b]) => a.localeCompare(b))
				.map(([country, items]) => ({
					country,
					items: items.sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf()),
				})),
		};
	});
}

export type ArchiveDay = {
	key: string;
	date: Date;
	count: number;
};

export type NewsFilterOptions = {
	languages: string[];
	continents: string[];
	countries: string[];
	sources: string[];
};

/** Distinct filter values present in the given entries. */
export function collectFilterOptions(entries: NewsEntry[]): NewsFilterOptions {
	const languages = new Set<string>();
	const continents = new Set<string>();
	const countries = new Set<string>();
	const sources = new Set<string>();

	for (const entry of entries) {
		languages.add(entry.data.languageName);
		continents.add(entry.data.continent);
		countries.add(entry.data.country);
		sources.add(entry.data.source);
	}

	return {
		languages: [...languages].sort((a, b) => a.localeCompare(b)),
		continents: CONTINENT_ORDER.filter((c) => continents.has(c)),
		countries: [...countries].sort((a, b) => a.localeCompare(b)),
		sources: [...sources].sort((a, b) => a.localeCompare(b)),
	};
}

/** Unique dates newest-first, with article counts. */
export function buildArchive(entries: NewsEntry[]): ArchiveDay[] {
	const counts = new Map<string, { date: Date; count: number }>();

	for (const entry of entries) {
		const key = dateKey(entry.data.date);
		const existing = counts.get(key);
		if (existing) {
			existing.count += 1;
		} else {
			counts.set(key, { date: entry.data.date, count: 1 });
		}
	}

	return [...counts.entries()]
		.map(([key, { date, count }]) => ({ key, date, count }))
		.sort((a, b) => b.key.localeCompare(a.key));
}
