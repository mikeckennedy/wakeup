import aiohttp
from xml.etree import ElementTree
from unsync import unsync


def main():
    pass


def get_sitemap_text(self):
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
    res = self.app.get("/sitemap.xml")
    text = res.text.replace(' xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"', '')
    return text


def test_site_mapped_urls(self):
    text = self.get_sitemap_text()
    x = ElementTree.fromstring(text)
    urls = [
        href.text.strip().replace('http://training.talkpython.fm', '')
        for href in list(x.findall('url/loc'))
    ]
    print('Testing {} urls from sitemap...'.format(len(urls)), flush=True)

    has_tested_transcripts = False
    for url in urls:
        if url.find('courses/transcript') >= 0 and has_tested_transcripts:
            continue

        print('Testing url at ' + url)
        if not url.find('/courses/details') >= 0:
            self.app.get(url, status=200)
        else:
            self.app.get(url, status=302)

        if url.find('courses/transcript') >= 0:
            has_tested_transcripts = True


if __name__ == '__main__':
    main()
