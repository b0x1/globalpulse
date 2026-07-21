import os
import sys
import re
import urllib.request
import xml.etree.ElementTree as ET
import html
import datetime

# Target counts
TARGETS = {
    'en': 15,
    'de': 12,
    'fr': 12,
    'zh': 11
}

# RSS feeds map
RSS_FEEDS = {
    'bbc-news': 'https://feeds.bbci.co.uk/news/world/rss.xml',
    'the-guardian': 'https://www.theguardian.com/uk/rss',
    'nytimes': 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
    'cbc-news': 'https://rss.cbc.ca/lineup/topstories.xml',
    'abc-australia': 'https://www.abc.net.au/news/feed/51120/rss.xml',
    'rnz': 'https://www.rnz.co.nz/rss/news.xml',
    'rte': 'https://www.rte.ie/news/rss/news-headlines.xml',
    'tagesschau': 'https://www.tagesschau.de/xml/rss2/',
    'spiegel': 'https://www.spiegel.de/index.rss',
    'faz': 'https://www.faz.net/rss/aktuell/',
    'nzz': 'https://www.nzz.ch/recent.rss',
    'der-standard': 'https://www.derstandard.at/rss',
    'le-monde': 'https://www.lemonde.fr/rss/une.xml',
    'le-figaro': 'https://www.lefigaro.fr/rss/figaro_actualites.xml',
    'france24': 'https://www.france24.com/fr/rss',
    'franceinfo': 'https://www.francetvinfo.fr/titres.rss',
    'le-temps': 'https://www.letemps.ch/feed',
}

# Parse news-sources.yaml
def parse_sources(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    sources = []
    current = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('- '):
            if current:
                sources.append(current)
                current = {}
            line = line[2:]
        if ':' in line:
            parts = line.split(':', 1)
            key = parts[0].strip()
            val = parts[1].strip()
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            current[key] = val
    if current:
        sources.append(current)
    return sources

def clean_html(text):
    if not text:
        return ""
    # decode html entities first so we can remove any encoded tags like &lt;img ... &gt;
    text = html.unescape(text)
    # remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # clean extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_paragraph_content(text):
    """
    Cleans paragraphs and strips out any remaining scraping artifacts, css, paywall noise,
    or boilerplate. Returns None if paragraph is deemed junk.
    """
    text = clean_html(text)
    if not text:
        return None

    # Check for raw CSS blocks or bracket template tags
    if '{' in text or '}' in text or '@media' in text or 'margin:' in text or 'padding:' in text or '[!--' in text:
        return None

    # Check length
    if len(text) < 40:
        return None

    # Standard boilerplate/ad/paywall phrases in German, English, French, Chinese
    boilerplate = [
        'cookie', 'newsletter', 'abo', 'abonner', 'suivez-nous', 'copyright', 'tous droits',
        'figaro', 'spiegel', 'tagesschau', 'terms of', 'privacy policy', 'sie entscheiden darüber',
        'ihr gerät erlaubt', 'sie wollen', 'pour sauvegarder un article', 'vous devez être connecté',
        'les abonnés', 'partager cette info', 'en savoir plus', 'schon registriert', 'anmeldung',
        'einloggen', 'registrieren', 'passwort', 'benutzername', 'leserbrief', 'abo abschließen',
        'wir empfehlen auch', 'mehr zum thema', 'lesenswerte artikel', 'schreiben sie uns',
        'adblocker', 'blockieren', 'hard- und software-komponenten', 'deaktivieren',
        'abcclose', 'abc news', 'abc iview', 'search options', 'accessibility', 'sign in', 'log in',
        'subscription', 'subscribe', 'exclusive content', 'registrieren sie sich', 'kostenlos testen',
        'monatlich kündbar', '0,99 €', '13,80 €', 'eur/monat', 'eur', 'partagez cet article',
        'article réservé aux abonnés', 'offrir cet article', 'limiter le blocage', 'un robot',
        '违法和不良信息', '版权所有', '未有相关相关', '客户端下载', '扫码关注', '关注我们'
    ]

    text_lower = text.lower()
    for word in boilerplate:
        if word in text_lower:
            return None

    return text

def make_slug(source_id, title):
    slug_base = title.lower()
    slug_base = re.sub(r'[^\w\s-]', '', slug_base)
    slug_base = re.sub(r'[\s_]+', '-', slug_base)
    slug_base = re.sub(r'-+', '-', slug_base).strip('-')
    words = slug_base.split('-')[:5]
    slug_words = "-".join(words)
    if not slug_words:
        slug_words = "article"
    return f"{source_id}-{slug_words}"

def fetch_url(url, timeout=5):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get('Content-Type', '')
            charset = 'utf-8'
            if 'charset=' in content_type:
                charset = content_type.split('charset=')[-1].strip()
            data = resp.read()
            try:
                return data.decode(charset, errors='ignore')
            except:
                return data.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None

def parse_rss(xml_str):
    if not xml_str:
        return []
    try:
        items = []
        item_blocks = re.findall(r'<item[^>]*>(.*?)</item>', xml_str, re.DOTALL)
        for block in item_blocks:
            t_match = re.search(r'<title[^>]*>(.*?)</title>', block, re.DOTALL)
            l_match = re.search(r'<link[^>]*>(.*?)</link>', block, re.DOTALL)
            g_match = re.search(r'<guid[^>]*>(.*?)</guid>', block, re.DOTALL)
            d_match = re.search(r'<description[^>]*>(.*?)</description>', block, re.DOTALL)

            if t_match and (l_match or g_match):
                title = clean_html(t_match.group(1))
                link = l_match.group(1).strip() if l_match else g_match.group(1).strip()
                if title.startswith('<![CDATA[') and title.endswith(']]>'):
                    title = title[9:-3].strip()
                if link.startswith('<![CDATA[') and link.endswith(']]>'):
                    link = link[9:-3].strip()
                if not link.startswith('http') and g_match:
                    guid_text = g_match.group(1).strip()
                    if guid_text.startswith('http'):
                        link = guid_text
                desc = ""
                if d_match:
                    desc_text = d_match.group(1).strip()
                    if desc_text.startswith('<![CDATA[') and desc_text.endswith(']]>'):
                        desc_text = desc_text[9:-3].strip()
                    desc = clean_html(desc_text)
                if title and link.startswith('http'):
                    items.append({'title': title, 'link': link, 'desc': desc})
        return items
    except Exception as e:
        print(f"Error parsing RSS items: {e}", file=sys.stderr)
        return []

def main():
    sources = parse_sources('src/data/news-sources.yaml')
    sources_by_id = {s['id']: s for s in sources}
    print(f"Loaded {len(sources)} sources.")

    # Dynamically determine today's date
    today_date = datetime.datetime.now(datetime.timezone.utc).date()
    yyyy_mm_dd = today_date.strftime("%Y-%m-%d")
    yyyy_mm_dd_slash = today_date.strftime("%Y/%m/%d")
    yyyymmdd = today_date.strftime("%Y%m%d")
    yyyy = today_date.strftime("%Y")
    print(f"Today's date is calculated as: {yyyy_mm_dd}")

    # We will gather articles by language
    gathered = {
        'en': [],
        'de': [],
        'fr': [],
        'zh': []
    }

    # 1. English
    print("\n--- GATHERING ENGLISH ---")
    en_sources = [s for s in sources if s['language'] == 'en']
    for s in en_sources:
        sid = s['id']
        if len(gathered['en']) >= TARGETS['en']:
            break
        feed_url = RSS_FEEDS.get(sid)
        if feed_url:
            print(f"Fetching RSS for {sid}...")
            xml_str = fetch_url(feed_url)
            items = parse_rss(xml_str)
            print(f"Found {len(items)} items.")
            count = 0
            for item in items:
                if count >= 3:
                    break

                # To guarantee 100% clean paragraphs, we use the beautiful RSS description!
                desc_p = clean_paragraph_content(item['desc'])
                if not desc_p:
                    desc_p = item['title']

                gathered['en'].append({
                    'source_id': sid,
                    'title': item['title'],
                    'description': item['desc'] or item['title'],
                    'url': item['link'],
                    'paragraphs': [desc_p]
                })
                count += 1
                print(f"    Added. (Total EN: {len(gathered['en'])}/{TARGETS['en']})")
                if len(gathered['en']) >= TARGETS['en']:
                    break

    # 2. German
    print("\n--- GATHERING GERMAN ---")
    de_sources = [s for s in sources if s['language'] == 'de']
    for s in de_sources:
        sid = s['id']
        if len(gathered['de']) >= TARGETS['de']:
            break
        feed_url = RSS_FEEDS.get(sid)
        if feed_url:
            print(f"Fetching RSS for {sid}...")
            xml_str = fetch_url(feed_url)
            items = parse_rss(xml_str)
            print(f"Found {len(items)} items.")
            count = 0
            for item in items:
                if count >= 3:
                    break

                desc_p = clean_paragraph_content(item['desc'])
                if not desc_p:
                    desc_p = item['title']

                gathered['de'].append({
                    'source_id': sid,
                    'title': item['title'],
                    'description': item['desc'] or item['title'],
                    'url': item['link'],
                    'paragraphs': [desc_p]
                })
                count += 1
                print(f"    Added. (Total DE: {len(gathered['de'])}/{TARGETS['de']})")
                if len(gathered['de']) >= TARGETS['de']:
                    break

    # 3. French
    print("\n--- GATHERING FRENCH ---")
    fr_sources = [s for s in sources if s['language'] == 'fr']
    for s in fr_sources:
        sid = s['id']
        if len(gathered['fr']) >= TARGETS['fr']:
            break
        feed_url = RSS_FEEDS.get(sid)
        if feed_url:
            print(f"Fetching RSS for {sid}...")
            xml_str = fetch_url(feed_url)
            items = parse_rss(xml_str)
            print(f"Found {len(items)} items.")
            count = 0
            for item in items:
                if count >= 3:
                    break

                desc_p = clean_paragraph_content(item['desc'])
                if not desc_p:
                    desc_p = item['title']

                gathered['fr'].append({
                    'source_id': sid,
                    'title': item['title'],
                    'description': item['desc'] or item['title'],
                    'url': item['link'],
                    'paragraphs': [desc_p]
                })
                count += 1
                print(f"    Added. (Total FR: {len(gathered['fr'])}/{TARGETS['fr']})")
                if len(gathered['fr']) >= TARGETS['fr']:
                    break
        elif sid == 'la-presse':
            print(f"Scraping La Presse...")
            html_str = fetch_url('https://www.lapresse.ca/actualites/')
            if html_str:
                links = set(re.findall(r'href=\"(https://www\.lapresse\.ca/actualites/[^\"]+\.php)\"', html_str))
                print(f"Found {len(links)} La Presse links.")
                count = 0
                for link in sorted(list(links))[:3]:
                    art_html = fetch_url(link)
                    if art_html:
                        t_match = re.search(r'<title[^>]*>(.*?)</title>', art_html)
                        d_match = re.search(r'<meta name=\"description\" content=\"(.*?)\"', art_html)
                        title = clean_html(t_match.group(1)) if t_match else "Actualité La Presse"
                        if " | " in title:
                            title = title.split(" | ")[0].strip()
                        desc = clean_html(d_match.group(1)) if d_match else ""

                        desc_p = clean_paragraph_content(desc)
                        if not desc_p:
                            desc_p = title

                        gathered['fr'].append({
                            'source_id': sid,
                            'title': title,
                            'description': desc or title,
                            'url': link,
                            'paragraphs': [desc_p]
                        })
                        count += 1
                        print(f"    Added La Presse article: {title[:50]}...")
                        if len(gathered['fr']) >= TARGETS['fr']:
                            break

    # 4. Chinese
    print("\n--- GATHERING CHINESE ---")
    zh_sources = [s for s in sources if s['language'] == 'zh']
    for s in zh_sources:
        sid = s['id']
        if len(gathered['zh']) >= TARGETS['zh']:
            break
        print(f"Processing Chinese source {sid} ({s['url']})...")
        homepage_html = fetch_url(s['url'])
        if not homepage_html:
            continue

        # Extract links
        links = []
        if sid == 'xinhua':
            links = set(re.findall(r'href=\"(https?://www\.news\.cn/[^\"]+c\.html)\"', homepage_html))
        elif sid == 'people-cn':
            links = set(re.findall(rf'href=\"(http://society\.people\.com\.cn/n1/{yyyy}/[^\"]+\.html|http://finance\.people\.com\.cn/n1/{yyyy}/[^\"]+\.html)\"', homepage_html))
        elif sid == 'cctv-news':
            links = set(re.findall(rf'href=\"(https?://news\.cctv\.com/{yyyy_mm_dd_slash}/[^\"]+\.shtml)\"', homepage_html))
        elif sid == 'lianhe-zaobao':
            raw_links = set(re.findall(rf'href=\"(/news/singapore/story{yyyymmdd}-[^\"]+|/news/china/story{yyyymmdd}-[^\"]+|/news/world/story{yyyymmdd}-[^\"]+)\"', homepage_html))
            links = ["https://www.zaobao.com.sg" + l for l in raw_links]
        elif sid == 'udn':
            raw_links = set(re.findall(r'href=\"([^\"]*story\d+/\d+)\"', homepage_html))
            links = [l for l in raw_links if 'udn.com/news/story' in l]
        elif sid == 'ltn':
            links = set(re.findall(r'href=\"(https://news\.ltn\.com\.tw/news/[a-z]+/breakingnews/\d+)\"', homepage_html))
        elif sid == 'caixin':
            links = set(re.findall(rf'href=\"(https://[a-z]+\.caixin\.com/{yyyy_mm_dd}/[^\"]+\.html)\"', homepage_html))

        print(f"Found {len(links)} links for {sid}.")
        count = 0
        for link in list(links)[:3]:
            art_html = fetch_url(link)
            if art_html:
                t_match = re.search(r'<title[^>]*>(.*?)</title>', art_html)
                title = clean_html(t_match.group(1)) if t_match else ""
                if " | " in title:
                    title = title.split(" | ")[0].strip()
                elif " - " in title:
                    title = title.split(" - ")[0].strip()
                elif "—" in title:
                    title = title.split("—")[0].strip()
                elif "_" in title:
                    title = title.split("_")[0].strip()

                if not title.strip():
                    print("    Skipping Chinese article with empty title.")
                    continue

                d_match = re.search(r'<meta name=\"description\" content=\"(.*?)\"', art_html)
                desc = clean_html(d_match.group(1)) if d_match else ""

                desc_p = clean_paragraph_content(desc)
                if not desc_p:
                    desc_p = title

                gathered['zh'].append({
                    'source_id': sid,
                    'title': title,
                    'description': desc or title,
                    'url': link,
                    'paragraphs': [desc_p]
                })
                count += 1
                print(f"    Added Chinese article: {title[:30]}...")
                if len(gathered['zh']) >= TARGETS['zh']:
                    break

    # Save to Markdown
    out_dir = f'src/content/news/{yyyy_mm_dd}'
    os.makedirs(out_dir, exist_ok=True)

    # Clean output dir first to avoid stale/partially broken files
    for f in os.listdir(out_dir):
        if f.endswith('.md'):
            os.remove(os.path.join(out_dir, f))

    total_written = 0
    for lang, items in gathered.items():
        print(f"\nWriting {len(items)} items for '{lang}'...")
        for item in items:
            s_id = item['source_id']
            src_info = sources_by_id[s_id]
            slug = make_slug(s_id, item['title'])
            filepath = os.path.join(out_dir, f"{slug}.md")

            title_escaped = item['title'].replace('"', '\\"')
            desc_escaped = item['description'].replace('"', '\\"')

            content_lines = [
                "---",
                f'title: "{title_escaped}"',
                f'description: "{desc_escaped}"',
                f"date: {yyyy_mm_dd}",
                f"continent: {src_info['continent']}",
                f"country: {src_info['country']}",
                f"language: {lang}",
                f"languageName: {src_info['languageName']}",
                f"source: {src_info['name']}",
                f"sourceUrl: {item['url']}",
                "---",
                ""
            ]
            for p in item['paragraphs']:
                content_lines.append(p)
                content_lines.append("")

            with open(filepath, 'w', encoding='utf-8') as out_f:
                out_f.write("\n".join(content_lines))
            total_written += 1

    print(f"\nDone! Successfully wrote {total_written} news stories.")

if __name__ == '__main__':
    main()
