import os
import sys
import re
import urllib.request
import html
import datetime

# Target counts
TARGETS = {
    'en': 15,
    'de': 12,
    'fr': 12,
    'zh': 11
}

PER_SOURCE_LIMIT = 3


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


def strip_title_suffix(title):
    for sep in (' | ', ' - ', '—', '_'):
        if sep in title:
            return title.split(sep)[0].strip()
    return title


def make_article(source_id, title, description, url):
    desc = description or title
    desc_p = clean_paragraph_content(desc)
    if not desc_p:
        desc_p = title
    return {
        'source_id': source_id,
        'title': title,
        'description': desc,
        'url': url,
        'paragraphs': [desc_p],
    }


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
            except Exception:
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


def scrape_article_page(url, fallback_title=''):
    art_html = fetch_url(url)
    if not art_html:
        return None
    t_match = re.search(r'<title[^>]*>(.*?)</title>', art_html)
    title = clean_html(t_match.group(1)) if t_match else fallback_title
    title = strip_title_suffix(title)
    d_match = re.search(r'<meta name="description" content="(.*?)"', art_html)
    desc = clean_html(d_match.group(1)) if d_match else ''
    return title, desc


def gather_from_rss(sources, lang, target, bucket):
    for s in sources:
        if len(bucket) >= target:
            break
        feed_url = s.get('rssUrl')
        if not feed_url:
            continue
        sid = s['id']
        print(f"Fetching RSS for {sid}...")
        xml_str = fetch_url(feed_url)
        items = parse_rss(xml_str)
        print(f"Found {len(items)} items.")
        for item in items[:PER_SOURCE_LIMIT]:
            bucket.append(make_article(sid, item['title'], item['desc'], item['link']))
            print(f"    Added. (Total {lang.upper()}: {len(bucket)}/{target})")
            if len(bucket) >= target:
                break


def scrape_la_presse(bucket, target):
    if len(bucket) >= target:
        return
    print("Scraping La Presse...")
    html_str = fetch_url('https://www.lapresse.ca/actualites/')
    if not html_str:
        return
    links = set(re.findall(r'href="(https://www\.lapresse\.ca/actualites/[^"]+\.php)"', html_str))
    print(f"Found {len(links)} La Presse links.")
    for link in sorted(links)[:PER_SOURCE_LIMIT]:
        scraped = scrape_article_page(link, fallback_title='Actualité La Presse')
        if not scraped:
            continue
        title, desc = scraped
        if not title:
            title = 'Actualité La Presse'
        bucket.append(make_article('la-presse', title, desc, link))
        print(f"    Added La Presse article: {title[:50]}...")
        if len(bucket) >= target:
            break


def extract_zh_links(sid, homepage_html, today):
    yyyy = today.strftime('%Y')
    yyyy_mm_dd = today.strftime('%Y-%m-%d')
    yyyy_mm_dd_slash = today.strftime('%Y/%m/%d')
    yyyymmdd = today.strftime('%Y%m%d')

    if sid == 'xinhua':
        return set(re.findall(r'href="(https?://www\.news\.cn/[^"]+c\.html)"', homepage_html))
    if sid == 'people-cn':
        return set(re.findall(
            rf'href="(http://society\.people\.com\.cn/n1/{yyyy}/[^"]+\.html|http://finance\.people\.com\.cn/n1/{yyyy}/[^"]+\.html)"',
            homepage_html,
        ))
    if sid == 'cctv-news':
        return set(re.findall(
            rf'href="(https?://news\.cctv\.com/{yyyy_mm_dd_slash}/[^"]+\.shtml)"',
            homepage_html,
        ))
    if sid == 'lianhe-zaobao':
        raw_links = set(re.findall(
            rf'href="(/news/singapore/story{yyyymmdd}-[^"]+|/news/china/story{yyyymmdd}-[^"]+|/news/world/story{yyyymmdd}-[^"]+)"',
            homepage_html,
        ))
        return ["https://www.zaobao.com.sg" + l for l in raw_links]
    if sid == 'udn':
        raw_links = set(re.findall(r'href="([^"]*story\d+/\d+)"', homepage_html))
        return [l for l in raw_links if 'udn.com/news/story' in l]
    if sid == 'ltn':
        return set(re.findall(
            r'href="(https://news\.ltn\.com\.tw/news/[a-z]+/breakingnews/\d+)"',
            homepage_html,
        ))
    if sid == 'caixin':
        return set(re.findall(
            rf'href="(https://[a-z]+\.caixin\.com/{yyyy_mm_dd}/[^"]+\.html)"',
            homepage_html,
        ))
    return []


def gather_chinese(sources, target, bucket, today):
    for s in sources:
        if len(bucket) >= target:
            break
        sid = s['id']
        print(f"Processing Chinese source {sid} ({s['url']})...")
        homepage_html = fetch_url(s['url'])
        if not homepage_html:
            continue

        links = extract_zh_links(sid, homepage_html, today)
        print(f"Found {len(links)} links for {sid}.")
        for link in list(links)[:PER_SOURCE_LIMIT]:
            scraped = scrape_article_page(link)
            if not scraped:
                continue
            title, desc = scraped
            if not title.strip():
                print("    Skipping Chinese article with empty title.")
                continue
            bucket.append(make_article(sid, title, desc, link))
            print(f"    Added Chinese article: {title[:30]}...")
            if len(bucket) >= target:
                break


def write_stories(out_dir, gathered, sources_by_id, date):
    os.makedirs(out_dir, exist_ok=True)

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
                f"date: {date}",
                f"continent: {src_info['continent']}",
                f"country: {src_info['country']}",
                f"language: {lang}",
                f"languageName: {src_info['languageName']}",
                f"source: {src_info['name']}",
                f"sourceUrl: {item['url']}",
                "---",
                "",
            ]
            for p in item['paragraphs']:
                content_lines.append(p)
                content_lines.append("")

            with open(filepath, 'w', encoding='utf-8') as out_f:
                out_f.write("\n".join(content_lines))
            total_written += 1

    return total_written


def main():
    sources = parse_sources('src/data/news-sources.yaml')
    sources_by_id = {s['id']: s for s in sources}
    print(f"Loaded {len(sources)} sources.")

    today_date = datetime.datetime.now(datetime.timezone.utc).date()
    yyyy_mm_dd = today_date.strftime("%Y-%m-%d")
    print(f"Today's date is calculated as: {yyyy_mm_dd}")

    gathered = {lang: [] for lang in TARGETS}

    for lang in ('en', 'de', 'fr'):
        print(f"\n--- GATHERING {lang.upper()} ---")
        lang_sources = [s for s in sources if s['language'] == lang]
        gather_from_rss(lang_sources, lang, TARGETS[lang], gathered[lang])

    scrape_la_presse(gathered['fr'], TARGETS['fr'])

    print("\n--- GATHERING CHINESE ---")
    zh_sources = [s for s in sources if s['language'] == 'zh']
    gather_chinese(zh_sources, TARGETS['zh'], gathered['zh'], today_date)

    out_dir = f'src/content/news/{yyyy_mm_dd}'
    total_written = write_stories(out_dir, gathered, sources_by_id, yyyy_mm_dd)
    print(f"\nDone! Successfully wrote {total_written} news stories.")


if __name__ == '__main__':
    main()
