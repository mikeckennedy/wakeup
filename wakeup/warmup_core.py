import argparse
import statistics
import sys
import time
from collections import defaultdict, namedtuple
from typing import List, Final
from xml.etree import ElementTree

import aiohttp
from colorama import Fore
from unsync import unsync

Args = namedtuple('Args', 'sitemap_url, workers, ignore_patterns')
RequestResult = namedtuple('RequestResult', 'status, time_ms')


def __get_platform():
    platforms = {
        'linux1': 'Linux',
        'linux2': 'Linux',
        'darwin': 'OS X',
        'win32': 'Windows'
    }
    if sys.platform not in platforms:
        return sys.platform

    return platforms[sys.platform]


VER: sys.version_info = sys.version_info
PLATFORM: Final[str] = __get_platform()


def main():
    print(Fore.WHITE)

    args = get_params()
    print_header(args.sitemap_url, args.workers)

    # noinspection PyUnresolvedReferences
    sitemap = get_sitemap_text(args.sitemap_url).result()
    urls = get_site_mapped_urls(sitemap)

    filtered_urls = get_filtered_urls(urls, args.ignore_patterns)

    print(Fore.YELLOW + f"Testing {len(filtered_urls):,} total URLs.")
    print()
    print()
    print(Fore.WHITE + "*" * 50)
    print()
    print(Fore.LIGHTGREEN_EX + 'Running with one worker to wake systems...'.upper() + Fore.WHITE)
    print()
    run_url_requests(1, filtered_urls, Fore.LIGHTGREEN_EX + 'First request')
    print()
    print("*" * 50)
    print()
    print(Fore.WHITE + Fore.YELLOW + f'Running full power with {args.workers} workers...'.upper() + Fore.WHITE)
    print()
    run_url_requests(args.workers, filtered_urls, Fore.LIGHTRED_EX + 'Full power')


def run_url_requests(workers: int, filtered_urls: List[str], prefix: str):
    all_results = {}
    total = len(filtered_urls)
    for idx, url in enumerate(filtered_urls, start=1):
        if prefix:
            print(prefix, end=': ')
        print(Fore.WHITE + f"{idx}/{total}: Testing url, {workers:,} workers: {url}...", flush=True)
        # noinspection PyUnresolvedReferences
        results = test_url(url, workers).result()
        summary_page_result(results)
        all_results[url] = results
        print(flush=True)

        # Give the server a little break to handle any requests that may have backed up.
        time.sleep(.05)


def get_params():
    parser = argparse.ArgumentParser(description='Site warmup -- preload all public pages')
    parser.add_argument('sitemap_url', type=str, help='Url for sitemap, e.g. https://site.com/sitemap.xml')
    parser.add_argument('workers', type=int, help='Number of workers (concurrent requests)')
    parser.add_argument("ignore_patterns", nargs='*', type=str,
                        help="Substrings for URLs to only request once (zero or more args)",
                        default=[])

    args = parser.parse_args()

    return Args(args.sitemap_url, args.workers, args.ignore_patterns)


def print_header(sitemap_url: str, workers: int):
    start = sitemap_url.index('://') + 3
    end = start + sitemap_url[start:].index('/')
    domain = sitemap_url[start:end]

    print()
    print(' ---------------------------------------------------------')
    print('|                                                         |')
    print('|                     SITE WARM-UP                        |')
    print('|           github.com/mikeckennedy/wakeup                |')
    print('|                                                         |')
    print(' ---------------------------------------------------------')
    print()
    print(f'Testing {domain} with {workers} workers.')
    print()


def summary_page_result(results: List[RequestResult]):
    statuses = {r.status for r in results}
    times = [r.time_ms for r in results]
    min_time_ms = min(times)
    max_time_ms = max(times)
    med_time = statistics.median(times)

    bad_statuses = False
    for s in statuses:
        if 400 <= s <= 599:
            bad_statuses = True
            break

    if bad_statuses:
        print(Fore.RED, end='')
        print(f"Statuses: {statuses}")

    if med_time < .5:
        print(Fore.GREEN, end='')
    elif med_time < 1.5:
        print(Fore.YELLOW, end='')
    else:
        print(Fore.RED, end='')

    print("Times: min: {:,.2f}, median: {:,.2f}, max: {:,.2f}".format(
        min_time_ms, med_time, max_time_ms
    ))


@unsync
async def test_url(url: str, workers: int) -> List[RequestResult]:
    tasks = [
        async_get(url)
        for _ in range(0, workers)
    ]

    # noinspection PyUnresolvedReferences
    return [
        await t
        for t in tasks
    ]


@unsync
async def async_get(url) -> RequestResult:
    headers = {
        'User-Agent': f'Warmup client; {PLATFORM}; Python {VER.major}.{VER.minor}.{VER.micro}'
    }

    t0 = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            time_in_ms = time.time() - t0

    return RequestResult(resp.status, time_in_ms)


def get_filtered_urls(urls: List[str], once_patterns: List[str]) -> List[str]:
    filtered = []
    once_lookup = defaultdict(lambda: False)
    for u in urls:

        match_found = False
        matching_pattern = None
        for p in once_patterns:
            if p in u:
                match_found = True
                matching_pattern = p
                break

        if not match_found or not once_lookup[matching_pattern]:
            filtered.append(u)

        if matching_pattern:
            once_lookup[matching_pattern] = True

    return filtered


@unsync
async def get_sitemap_text(sitemap_url: str) -> str:
    # <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    #     <url>
    #         <loc>http://talkpython.fm/episodes/show/37/python-cybersecurity-and-penetration-testing</loc>
    #         <lastmod>2015-12-08</lastmod>
    #         <changefreq>weekly</changefreq>
    #         <priority>1.0</priority>
    #     </url>
    #     <url>
    #         ...
    #     </url>
    async with aiohttp.ClientSession() as session:
        async with session.get(sitemap_url) as resp:
            resp.raise_for_status()
            text = await resp.text()

    # namespaces, ugh.
    text = text.replace(' xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"', '')
    return text


def get_site_mapped_urls(sitemap_text: str) -> List[str]:
    x = ElementTree.fromstring(sitemap_text)
    urls = [
        href.text.strip()
        for href in list(x.findall('url/loc'))
    ]

    return urls


if __name__ == '__main__':
    main()
