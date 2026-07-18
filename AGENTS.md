# GlobalPulse

Astro site that aggregates news from different regions of the world, from local sources, in the **language of the land**.

## Product rules

- **Languages only:** English (`en`), German (`de`), Chinese (`zh`), French (`fr`). Do not add other languages unless asked.
- **Language of the land:** headlines and body text should be in that country’s local language (one of the four above), not translations into a single default language.
- **Landing (`/`):** list of news (title + short description when present), sectioned by **continent**, then **country**. Content comes from Markdown in `src/content/news/`.
- **Archive (`/archive`):** list of dates; `/archive/[date]` shows that day’s headlines.
- **Article (`/news/[...id]`):** full Markdown story.
- Prefer a clean scaffold over sample/filler content unless the user asks for examples.
- Current visual direction is good — preserve the existing look and feel unless asked to redesign.

## Content

Stories live in `src/content/news/YYYY-MM-DD/<slug>.md`. Schema is in `src/content.config.ts`. Helpers for grouping and archive dates are in `src/lib/news.ts`.

## News gathering

When looking for stories, use the curated outlet list in [`src/data/news-sources.yaml`](src/data/news-sources.yaml).

Rules for agents:

- Only use sources from that file (or ask before adding a new outlet).
- Match `language` / `languageName` / `country` / `continent` on each story to the chosen source.
- Prefer the local-language homepage/section listed (`en`, `de`, `zh`, `fr`) — not a translated international edition.
- Attribute `source` and `sourceUrl` from the list entry.
- Cover multiple continents when possible; do not over-sample a single country.
- **Daily volume:** fewer than **100** stories per day (hard max 99; target 40–80).

### Jules scheduled tasks

Copy-paste prompts (or point Jules at these files):

| Cadence | Instruction |
| --- | --- |
| Daily | [`jules/daily-gather-news.md`](jules/daily-gather-news.md) |
| Weekly | [`jules/weekly-review-sources.md`](jules/weekly-review-sources.md) |

## Development

When starting the dev server, use background mode:

```
astro dev --background
```

Manage the background server with `astro dev stop`, `astro dev status`, and `astro dev logs`.

## Documentation

Full documentation: https://docs.astro.build

Consult these guides before working on related tasks:

- [Adding pages, dynamic routes, or middleware](https://docs.astro.build/en/guides/routing/)
- [Working with Astro components](https://docs.astro.build/en/basics/astro-components/)
- [Using React, Vue, Svelte, or other framework components](https://docs.astro.build/en/guides/framework-components/)
- [Adding or managing content](https://docs.astro.build/en/guides/content-collections/)
- [Adding styles or using Tailwind](https://docs.astro.build/en/guides/styling/)
- [Supporting multiple languages](https://docs.astro.build/en/guides/internationalization/)
