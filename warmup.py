from collections import defaultdict, namedtuple
from typing import List
import time

import aiohttp
from xml.etree import ElementTree
from unsync import unsync

RequestResult = namedtuple('RequestResult', 'code, time_ms')


def main():
    sitemap_url = 'https://training.talkpython.fm/sitemap.xml'
    once_patterns = ['/transcript/', ]
    workers = 12

    # noinspection PyUnresolvedReferences
    sitemap = get_sitemap_text(sitemap_url).result()
    urls = get_site_mapped_urls(sitemap)

    filtered_urls = get_filtered_urls(urls, once_patterns)
    for url in filtered_urls:
        print("Testing url, {:,} workers: {}...".format(workers, url), flush=True)
        # noinspection PyUnresolvedReferences
        results = test_url(url, workers).result()
        for r in results:
            print(r)
        print()


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
    t0 = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
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
