#!/usr/bin/env python3
"""Fetch and cache Odoo 20 source files for repeatable, read-only audits.

Default cache: <this-folder>/cache/20.0/
Only raw.githubusercontent.com URLs for the Odoo 20 branch are accepted.
The script never writes into the audited repository.
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, unquote
from urllib.request import Request, urlopen

DEFAULT_TTL_DAYS = 7
ALLOWED_HOST = 'raw.githubusercontent.com'


def fail(message: str, code: int = 2) -> None:
    print(f'source-cache: {message}', file=sys.stderr)
    raise SystemExit(code)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', help='Raw GitHub URL to an Odoo 20.0 source file')
    parser.add_argument('--refresh', action='store_true', help='download even if cached file is fresh')
    parser.add_argument('--max-age-days', type=float, default=DEFAULT_TTL_DAYS,
                        help=f'redownload cached files older than this many days (default: {DEFAULT_TTL_DAYS})')
    args = parser.parse_args()

    parsed = urlparse(args.url)
    if parsed.scheme != 'https' or parsed.hostname != ALLOWED_HOST:
        fail(f'only HTTPS URLs hosted on {ALLOWED_HOST} are allowed')
    # raw.githubusercontent.com/<owner>/<repo>/20.0/<path...>
    parts = [unquote(p) for p in parsed.path.split('/') if p]
    if len(parts) < 4 or parts[2] != '20.0':
        fail('URL must point to a file on an explicit 20.0 branch, e.g. odoo/odoo/20.0/...')
    if any(p in ('.', '..') or '\\' in p for p in parts):
        fail('URL path contains an invalid component')

    relative = Path('20.0', parts[0], parts[1], *parts[3:])
    cache_root = (Path(__file__).resolve().parents[2] / "cache").resolve()
    target = (cache_root / relative).resolve()
    if cache_root != target and cache_root not in target.parents:
        fail('resolved cache path escaped the cache directory')
    metadata = target.with_name(target.name + '.metadata.json')
    target.parent.mkdir(parents=True, exist_ok=True)

    fresh = False
    if target.is_file() and not args.refresh:
        age_days = max(0.0, (time.time() - target.stat().st_mtime) / 86400)
        fresh = age_days <= max(0.0, args.max_age_days)
    if fresh:
        print(str(target))
        return 0

    request = Request(args.url, headers={'User-Agent': 'odoo-module-auditor-source-cache/1.0'})
    try:
        with urlopen(request, timeout=30) as response:
            status = getattr(response, 'status', 200)
            if status != 200:
                fail(f'download returned HTTP {status}', 3)
            data = response.read()
            final_url = response.geturl()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        fail(f'download failed: {exc}', 3)

    temp = target.with_name(target.name + '.tmp')
    try:
        temp.write_bytes(data)
        temp.replace(target)
        metadata.write_text(json.dumps({
            'requested_url': args.url,
            'final_url': final_url,
            'branch': '20.0',
            'fetched_at_epoch': int(time.time()),
            'size_bytes': len(data),
        }, indent=2) + '\n', encoding='utf-8')
    finally:
        if temp.exists():
            temp.unlink()
    print(str(target))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
