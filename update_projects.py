#!/usr/bin/env python3
"""Keep the orb's project list in step with the Research page on the lab's UVA site.

Reads the project cards on the lab's Research page (one card group per theme) and the Research
menu labels, writes projects.json, and rewrites the project list in index.html (between the
projects:start and projects:end markers) and the "Research projects" number on the page. The orb,
its caption counter and its tour all read that list, so a new card on the Research page becomes a
new icon on the orb.

- Themes map to the orb's three rings by name (see AREAS). A card group with an unknown name goes on
  the ring with the fewest projects, and the run logs a warning.
- A project keeps the icon it already has in projects.json. A new project gets an icon from words in
  its title (see ICON_WORDS), or the generic headset icon. To change an icon, edit "icon" in
  projects.json; later runs keep it. Icon names are the keys of ICONS in index.html.
- If the page cannot be read, or no project cards are found, the files are left as they are.

Run once a day by .github/workflows/update-events.yml, with update_events.py.
Local use:  python update_projects.py --html saved-research-page.html
            python update_projects.py --render-only     (index.html from the current projects.json)
"""
import argparse
import html as H
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from uva_fetch import Refused, fetch, refused_warning

LAB = 'https://engineering.virginia.edu/labs-groups/omni-reality-cognition-lab'
SOURCE = LAB + '/research'
HERE = Path(__file__).parent
DATA = HERE / 'projects.json'
PAGE = HERE / 'index.html'
START, END = '<!-- projects:start -->', '<!-- projects:end -->'

# The orb's three rings, in order, with words that identify each theme's card group
AREAS = [
    ('road', ('road user', 'micromobility', 'street', 'transport', 'pedestrian', 'cycl', 'mobility')),
    ('train', ('training', 'trainer', 'immersive', 'education', 'learning')),
    ('sense', ('sensing', 'human state', 'physiolog', 'wellbeing', 'well-being')),
]
# Icons for new projects: the first entry with a word in the title wins
ICON_WORDS = [
    ('scooter', ('scooter',)),
    ('helmet', ('adolescent', 'teen', 'youth', 'child')),
    ('bike', ('bicycl', 'bike', 'cyclist')),
    ('walk', ('pedestrian', 'walking', 'crossing')),
    ('eye', ('eye tracking', 'eye-tracking', 'gaze', 'seeing')),
    ('roundabout', ('design review', 'roundabout', 'intersection', 'public involvement')),
    ('heart', ('patient', 'clinical', 'health', 'nurs', 'medic', 'cardiac', 'hospital')),
    ('shield', ('cyber', 'security')),
    ('signal', ('signal', 'traffic')),
    ('wheel', ('driver', 'driving', 'vehicle')),
]
DEFAULT_ICON = 'vr'
SKIP = re.compile(r'^(funded by|photo|figure|image|credit)\b', re.I)


def text(el):
    return re.sub(r'\s+', ' ', el.get_text(' ', strip=True)).strip() if el else ''


def norm(url):
    """Absolute URL without query or fragment, for matching cards to menu links."""
    u = urlsplit(urljoin(SOURCE + '/', url or ''))
    return f'{u.scheme}://{u.netloc}{u.path.rstrip("/")}'


def area_for(name, counts):
    low = name.lower()
    for key, words in AREAS:
        if any(w in low for w in words):
            return key, True
    return min(counts, key=lambda k: counts[k]), False


def icon_for(title):
    low = title.lower()
    for icon, words in ICON_WORDS:
        if any(w in low for w in words):
            return icon
    return DEFAULT_ICON


def parse_projects(html, old):
    soup = BeautifulSoup(html, 'html.parser')
    labels = {}
    for a in soup.select('nav a[href]'):
        href = norm(a['href'])
        if href.startswith(SOURCE + '/') and text(a):
            labels.setdefault(href, text(a))
    old_icons = {norm(p['url']): p.get('icon') for p in old.get('projects', []) if p.get('url')}
    projects, areas, warnings = [], {}, []
    counts = {key: 0 for key, _ in AREAS}
    for group in soup.select('.card_group'):
        gname = text(group.select_one('.card_group_title'))
        items = group.select('.card_group_item')
        if not gname or not items:
            continue
        area, known = area_for(gname, counts)
        if not known:
            warnings.append(f'Card group "{gname}" does not match a ring; its projects go on the "{area}" ring.')
        areas.setdefault(area, gname)
        for it in items:
            desc = it.select_one('.card_group_item_description')
            head = (desc.select_one('h3, h2, h4') if desc else None) or it.select_one('.card_group_item_title')
            link = (head.select_one('a[href]') if head else None) or it.select_one('a.card_group_item_link[href]')
            title = text(head)
            if not title or not link:
                continue
            url = norm(link['href'])
            sentence = ''
            for p in (desc.select('p') if desc else []):
                t = text(p)
                if t and not p.select_one('img') and not SKIP.match(t):
                    sentence = t
                    break
            icon = old_icons.get(url) or icon_for(title)
            projects.append({'title': title, 'label': labels.get(url, title), 'url': url,
                             'area': area, 'icon': icon, 'text': sentence})
            counts[area] += 1
    # Rings in their fixed order; projects keep the Research page's order within a ring
    order = {key: i for i, (key, _) in enumerate(AREAS)}
    projects.sort(key=lambda p: order[p['area']])
    return projects, {k: areas[k] for k, _ in AREAS if k in areas}, warnings


def attr(s):
    return H.escape(s, quote=False).replace('"', '&quot;')


def render_list(data):
    lines = ['      <div class="index-cols">']
    projects, i = data['projects'], 0
    for key, _ in AREAS:
        group = [p for p in projects if p['area'] == key]
        if not group:
            continue
        name = data.get('areas', {}).get(key, key)
        lines += [f'        <section class="area" data-area="{key}" aria-labelledby="area-{key}">',
                  f'          <h3 class="area-name" id="area-{key}">{H.escape(name, quote=False)}</h3>',
                  '          <ul>']
        for p in group:
            lines.append(f'            <li><a href="{attr(p["url"])}" data-i="{i}" data-icon="{attr(p["icon"])}" data-area="{key}" '
                         f'data-title="{attr(p["title"])}" aria-describedby="pd{i}">{H.escape(p["label"], quote=False)}</a></li>')
            i += 1
        lines += ['          </ul>', '        </section>']
    lines += ['      </div>', '      <div class="sr-only">']
    i = 0
    for key, _ in AREAS:
        for p in (q for q in projects if q['area'] == key):
            lines.append(f'        <p id="pd{i}">{H.escape(p["text"], quote=False)}</p>')
            i += 1
    lines.append('      </div>')
    return '\n'.join(lines)


def render_into(page, data):
    """Replace the project list between the markers and the "Research projects" number."""
    a, b = page.find(START), page.find(END)
    if a < 0 or b < a:
        raise SystemExit('index.html has no projects:start / projects:end markers')
    page = page[:a + len(START)] + '\n' + render_list(data) + '\n      ' + page[b:]
    return re.sub(r'(<p class="stat-num" data-stat="projects">)\d+(</p>)', rf'\g<1>{len(data["projects"])}\g<2>', page)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--html', help='parse this saved Research page instead of fetching the live one')
    ap.add_argument('--render-only', action='store_true', help='only rewrite index.html from the current projects.json')
    ap.add_argument('--data', default=str(DATA))
    ap.add_argument('--page', default=str(PAGE))
    a = ap.parse_args()
    data_path, page_path = Path(a.data), Path(a.page)
    old = json.loads(data_path.read_text(encoding='utf-8')) if data_path.exists() else {}

    if a.render_only:
        new = old
    else:
        try:
            html = Path(a.html).read_text(encoding='utf-8') if a.html else fetch(SOURCE)
        except Refused as r:
            refused_warning('projects.json and the orb were left as they are', r)
            return 0
        projects, areas, warnings = parse_projects(html, old)
        for w in warnings:
            print('::warning::' + w)
        if not projects:
            print('::warning::No project cards found on the Research page; projects.json and the orb were left as they are.')
            return 0
        new = {'source': SOURCE, 'updated': None, 'areas': areas, 'projects': projects}
        same = all(new[k] == old.get(k) for k in ('source', 'areas', 'projects'))
        new['updated'] = old['updated'] if same and old.get('updated') else \
            datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        before = {p['url']: p['title'] for p in old.get('projects', [])}
        after = {p['url']: p['title'] for p in projects}
        for u in after.keys() - before.keys():
            print(f'added: {after[u]}')
        for u in before.keys() - after.keys():
            print(f'removed: {before[u]}')
        print(f'{len(projects)} projects: ' + ', '.join(f'{p["label"]} ({p["area"]}, {p["icon"]})' for p in projects))
        if new != old:
            data_path.write_text(json.dumps(new, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            print('projects.json written')
        else:
            print('projects.json unchanged')

    page = page_path.read_text(encoding='utf-8')
    out = render_into(page, new)
    if out != page:
        page_path.write_text(out, encoding='utf-8')
        print('index.html project list rewritten')
    else:
        print('index.html unchanged')
    return 0


if __name__ == '__main__':
    sys.exit(main())
