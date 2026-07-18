# Jules — Daily news gather

**Schedule:** once per day (prefer morning in Europe/Vienna, or after local midnight UTC).

**Goal:** Add today’s headlines to GlobalPulse as Markdown stories, then open a PR.

Read `AGENTS.md` and `src/data/news-sources.yaml` before starting.

## Hard limits

- **Fewer than 100 stories** for the day (hard max **99**). Aim for **40–80** when sources allow.
- Languages only: **en**, **de**, **zh**, **fr**.
- Only outlets listed in `src/data/news-sources.yaml` (do not invent sources).
- Stories must be in the **language of the land** for that source (local-language edition).

## What to gather

1. Use today’s date (`YYYY-MM-DD`) as the story `date` for every file.
2. Pick a balanced mix across languages and continents. Rough targets within the daily cap:
   - ~25–35% English
   - ~20–25% German
   - ~20–25% French
   - ~20–25% Chinese
3. Prefer distinct countries; avoid flooding one outlet or one country.
4. Skip duplicates of stories already in `src/content/news/YYYY-MM-DD/` (same topic + source + day).
5. Prefer substantive local/national news over celebrity fluff, ads, or pure opinion columns.

## File format

Create one file per story under that day’s folder:

```text
src/content/news/YYYY-MM-DD/<short-slug>.md
```

Example: `src/content/news/2026-07-18/lemonde-taxe-logements-vacants.md`

Frontmatter must match `src/content.config.ts`:

```yaml
---
title: "Headline in the source language"
description: "Optional one-sentence summary in the same language"
date: YYYY-MM-DD
continent: Europe
country: France
language: fr
languageName: French
source: Le Monde
sourceUrl: https://www.lemonde.fr/
---

Short body (1–3 paragraphs) in the source language. Paraphrase or quote briefly;
do not paste an entire paywalled article.
```

- `language` / `languageName` / `country` / `continent` must match the chosen entry in `news-sources.yaml`.
- `source` = outlet `name`; `sourceUrl` = article URL when known, otherwise the outlet homepage URL from the list.

## Acceptance checklist

- [ ] Story count for today is **&lt; 100**
- [ ] Every story validates against the content schema
- [ ] `npm run build` succeeds
- [ ] No sample/filler content; no new languages; no sources outside the YAML list
- [ ] Open a PR titled: `news: YYYY-MM-DD daily gather (N stories)`

## Out of scope

- Do not redesign the site or change styles.
- Do not edit `src/data/news-sources.yaml` on the daily run (that is the weekly task).
- Do not commit secrets or scraped full copyrighted article dumps.
