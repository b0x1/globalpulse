# Jules — Weekly news-sources review

**Schedule:** once per week (prefer Monday).

**Goal:** Review and update `src/data/news-sources.yaml` so agents keep a healthy, accurate outlet list. Open a PR with the changes (or a short “no changes needed” note in the PR body if the list is already solid).

Read `AGENTS.md` and the current `src/data/news-sources.yaml` before starting.

## Scope

Only touch:

- `src/data/news-sources.yaml`
- `AGENTS.md` (only if gathering rules must change because of list updates)
- This file / `jules/daily-gather-news.md` only if a review finding requires clearer agent rules

Do **not** gather daily news in this task.

## Review checklist

1. **Alive links:** Spot-check every `url`. Fix or replace dead redirects; remove permanently dead outlets.
2. **Language of the land:** Confirm each entry points at the **local-language** edition (`en` / `de` / `zh` / `fr`), not a translated international mirror unless that is the land’s language.
3. **Coverage gaps:** Ensure the four languages and multiple continents are represented. Prefer adding strong local outlets over more mega-wires in the same country.
4. **Quality bar:** Keep reputable national/regional news orgs. Drop pure aggregators, SEO farms, or outlets that no longer publish original news.
5. **Metadata:** Keep fields consistent: `id`, `name`, `url`, `language`, `languageName`, `country`, `continent` (+ optional `notes`).
6. **Ids:** Stable kebab-case `id`s. Do not rename an `id` unless necessary (breaks agent habit); prefer fixing `url` / `name` instead.
7. **Size:** Keep the list practical — roughly **30–60** outlets. Add sparingly; remove clearly weak or redundant entries.

## Allowed languages / regions

- English, German, Chinese, French only.
- Countries where that language is a primary public language for news (language of the land).

## Acceptance checklist

- [ ] YAML is valid and consistently formatted
- [ ] No outlets outside en/de/zh/fr
- [ ] URLs use `https://` where available
- [ ] Brief PR summary: added / removed / fixed (with reasons)
- [ ] PR title: `sources: weekly review YYYY-MM-DD`

## Out of scope

- Do not add sample stories under `src/content/news/YYYY-MM-DD/`.
- Do not change site UI, schema, or routing unless required to keep the source list usable — and call that out explicitly in the PR.
