import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const news = defineCollection({
	loader: glob({ pattern: '**/*.md', base: './src/content/news' }),
	schema: z.object({
		title: z.string(),
		description: z.string().optional(),
		date: z.coerce.date(),
		continent: z.enum([
			'Africa',
			'Asia',
			'Europe',
			'North America',
			'South America',
			'Oceania',
		]),
		country: z.string(),
		language: z.enum(['en', 'de', 'zh', 'fr']),
		languageName: z.enum(['English', 'German', 'Chinese', 'French']),
		source: z.string(),
		sourceUrl: z.string().url().optional(),
		draft: z.boolean().default(false),
	}),
});

export const collections = { news };
