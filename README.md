# GlobalPulse

Astro scaffold for news in English, German, Chinese, and French — grouped by continent and country.

## Routes

| Route | Purpose |
| --- | --- |
| `/` | Landing — headlines by continent → country |
| `/archive` | Date list |
| `/archive/[date]` | Headlines for one day |
| `/news/[id]` | Article |

## Add a story

Create `src/content/news/your-slug.md`:

```yaml
---
title: "Headline"
description: "Optional summary"
date: 2026-07-18
continent: Europe
country: France
language: fr          # en | de | zh | fr
languageName: French  # English | German | Chinese | French
source: Le Monde
sourceUrl: https://www.lemonde.fr/
---

Body text…
```

## Commands

```sh
npm run dev
npm run build
npm run preview
```
