#!/usr/bin/env python3
"""Refresh events.json from the "Upcoming Events" list on the lab's UVA Engineering home page.

Run once a day by .github/workflows/update-events.yml. The page (index.html) loads events.json
and hides events that have ended. If the UVA site refuses the request (it sits behind Cloudflare,
which blocks automated requests unless UVA allows them), or the events block is missing, the old
file is kept and a warning is logged. Other fetch errors fail the run.

Local test:  python update_events.py --html saved-page.html --out /tmp/events.json
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

SOURCE = 'https://engineering.virginia.edu/labs-groups/omni-reality-cognition-lab'
OUT = Path(__file__).with_name('events.json')
ET = ZoneInfo('America/New_York')
UA = 'ORCL-events-updater/1.0 (+https://github.com/aheydarian/orcl-prism)'
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
TIME_RANGE = re.compile(r'(\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?)\s*[-–—]\s*(\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?)', re.I)


def text(el):
    return re.sub(r'\s+', ' ', el.get_text(' ', strip=True)).strip() if el else ''


def parse_dt(value):
    """'2026-10-06 13:00:00 America/New_York' -> aware datetime."""
    m = re.match(r'\s*(\d{4}-\d{2}-\d{2})(?:[ T](\d{1,2}:\d{2})(?::\d{2})?)?\s*(\S+)?', value or '')
    if not m:
        return None
    tz = ET
    if m.group(3) and '/' in m.group(3):
        try:
            tz = ZoneInfo(m.group(3))
        except Exception:
            pass
    return datetime.fromisoformat(f'{m.group(1)}T{m.group(2) or "00:00"}').replace(tzinfo=tz)


def clock(s):
    s = s.upper().replace('.', '').replace(' ', '')
    return datetime.strptime(s, '%I:%M%p' if ':' in s else '%I%p').time()


def parse_events(html, base=SOURCE):
    soup = BeautifulSoup(html, 'html.parser')
    sections = soup.select('.event_list_section')
    sec = next((s for s in sections if 'event' in text(s.select_one('.event_list_section_title')).lower()), None)
    if sec is None:
        return None
    cta = sec.select_one('a.event_list_section_cta_link[href]')
    out = {
        'intro': text(sec.select_one('.event_list_section_description')),
        'calendar': urljoin(base, cta['href']) if cta else '',
        'events': [],
    }
    for li in sec.select('.event_list_section-item'):
        link = li.select_one('a.event_list_item_title_link[href]')
        title = text(li.select_one('.event_list_item_title_link_label')) or text(link)
        times = [d for d in (parse_dt(t.get('datetime')) for t in li.select('time[datetime]')) if d]
        if not title or not times:
            continue
        start = times[0]
        details = {}
        for d in li.select('.event_list_item_detail'):
            hint = text(d.select_one('.event_list_item_detail_hint')).rstrip(':').strip().lower()
            label = text(d.select_one('.event_list_item_detail_label'))
            if hint and label:
                details[hint] = label
        time_label = details.get('time', '')
        end = None
        m = TIME_RANGE.search(time_label)
        if m:
            try:
                end = datetime.combine(start.date(), clock(m.group(2)), tzinfo=start.tzinfo)
                if end <= start:
                    end += timedelta(days=1)
            except ValueError:
                end = None
        if end is None:  # no clock range: the event lasts to the end of its last day
            last_day = max(t.date() for t in times)
            end = datetime.combine(last_day, datetime.min.time(), tzinfo=start.tzinfo) + timedelta(days=1) - timedelta(seconds=1)
        desc = ' '.join(t for t in (text(p) for p in li.select('.event_list_item_description p')) if t)
        out['events'].append({
            'title': title,
            'url': urljoin(base, link['href']) if link else out['calendar'],
            'start': start.isoformat(),
            'end': end.isoformat(),
            'month': MONTHS[start.month - 1],
            'day': f'{start.day:02d}',
            'when': text(li.select_one('.event_list_item_time_start')) or f'{MONTHS[start.month - 1]} {start.day:02d}',
            'time': time_label,
            'location': details.get('location', ''),
            'description': desc or text(li.select_one('.event_list_item_description')),
        })
    return out


class Refused(Exception):
    """The site answered, but refused this client (for example a Cloudflare block or challenge)."""


def fetch(url, tries=3):
    for i in range(tries):
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html'})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 429):
                body = e.read(6000).decode('utf-8', 'replace')
                m = re.search(r'<title[^>]*>(.*?)</title>', body, re.S | re.I)
                title = re.sub(r'\s+', ' ', m.group(1)).strip()[:80] if m else 'none'
                info = ', '.join(f'{k}: {e.headers.get(k)}' for k in ('server', 'cf-mitigated', 'cf-ray') if e.headers.get(k))
                raise Refused(f'HTTP {e.code}; {info or "no server headers"}; page title: {title}')
            err = e
        except Exception as e:  # network hiccup: wait and retry
            err = e
        print(f'fetch attempt {i + 1} failed: {err}', file=sys.stderr)
        if i == tries - 1:
            raise err
        time.sleep(20 * (i + 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--html', help='parse this saved page instead of fetching the live one')
    ap.add_argument('--out', default=str(OUT))
    a = ap.parse_args()

    try:
        html = Path(a.html).read_text(encoding='utf-8') if a.html else fetch(SOURCE)
    except Refused as r:
        print(f'::warning::The UVA site refused the request ({r}). events.json was left as it is. '
              'UVA web services can allow this updater (user agent ORCL-events-updater) on the lab page.')
        return 0
    out = Path(a.out)
    old = json.loads(out.read_text(encoding='utf-8')) if out.exists() else {}
    parsed = parse_events(html)
    if parsed is None:
        print('::warning::No "Upcoming Events" block found on the lab page; events.json left as it is.')
        return 0

    new = {
        'source': SOURCE,
        'updated': None,
        'calendar': parsed['calendar'] or old.get('calendar', ''),
        'intro': parsed['intro'] or old.get('intro', ''),
        'events': parsed['events'],
    }
    same = all(new[k] == old.get(k) for k in ('source', 'calendar', 'intro', 'events'))
    new['updated'] = old['updated'] if same and old.get('updated') else \
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    for e in new['events']:
        print(f"{e['start'][:16]}  {e['title']}  ({e['location']})")
    if not new['events']:
        print('No upcoming events listed on the lab page.')
    if new == old:
        print('events.json unchanged')
        return 0
    out.write_text(json.dumps(new, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'events.json written ({len(new["events"])} events)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
