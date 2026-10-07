"""Fetch a page from the lab's UVA Engineering site for the updaters, and report refusals.

The updaters identify themselves with the user agent below. engineering.virginia.edu sits behind
Cloudflare; until UVA web services allow this user agent, the site answers with 403, which the
updaters log as a warning while keeping their current files.
"""
import re
import sys
import time
import urllib.error
import urllib.request

UA = 'ORCL-site-updater/1.0 (+https://github.com/aheydarian/orcl-prism)'


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


def refused_warning(what, r):
    print(f'::warning::The UVA site refused the request ({r}). {what}. '
          'UVA web services can allow this updater (user agent ORCL-site-updater) on the lab\'s pages.')
