#!/usr/bin/python

from __future__ import unicode_literals, print_function, absolute_import
###########################################################################
#          (C) Vrije Universiteit, Amsterdam (the Netherlands)            #
#                                                                         #
# This file is part of AmCAT - The Amsterdam Content Analysis Toolkit     #
#                                                                         #
# AmCAT is free software: you can redistribute it and/or modify it under  #
# the terms of the GNU Affero General Public License as published by the  #
# Free Software Foundation, either version 3 of the License, or (at your  #
# option) any later version.                                              #
#                                                                         #
# AmCAT is distributed in the hope that it will be useful, but WITHOUT    #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or   #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public     #
# License for more details.                                               #
#                                                                         #
# You should have received a copy of the GNU Affero General Public        #
# License along with AmCAT.  If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################
# en_wikinews_org_scraper -- scrape en.wikinews.org
# 20121218 Paul Huygen
# 20140418 Wouter van Atteveldt

"""
Simple (and not terribly good) wikinews scraper

This scraper is provided as an exmample non-trivial scraper using
the AmCAT API as back-end, and to provide non-copyrighted text for examples
"""


from urlparse import urljoin
import re
import datetime
from lxml import html, etree


def get_pages(url):
    """
    Return the 'pages' from the starting url
    Technically, look for the 'next 200' link, yield and download it,  repeat
    """
    while True:
        yield url
        doc = html.parse(url).find("body")
        links = [a for a in doc.findall(".//a") if a.text == "next 200"]
        if not links:
            break
        url = urljoin(url, links[0].get('href'))

def get_articles(url):
    """
    Return the articles from a page
    Technically, look for id=mw-pages elements and yield the links from
    the list under those elements
    """
    doc = html.parse(url).find("body")
    for a in doc.findall(".//*[@id='mw-pages']//li/a"):
        href = urljoin(url, a.get('href'))
        yield href

def export_url(url):
    """
    Get the 'Special:Export' XML version url of an article
    """
    page = url.split("/")[-1]
    return ("http://en.wikinews.org/w/index.php?title=Special:Export"
            "&action=submit&pages={}".format(page))


def get_article(url):
    """
    Return a single article as a 'amcat-ready' dict
    Uses the 'export' function of wikinews to get an xml article
    """
    art = etree.parse(export_url(url))
    ns = {'x' : 'http://www.mediawiki.org/xml/export-0.8/'}
    title = art.find(".//x:title", namespaces=ns).text
    date = art.find(".//x:timestamp", namespaces=ns).text
    author = art.find(".//x:contributor/x:username", namespaces=ns).text
    id = int(art.find(".//x:page/x:id", namespaces=ns).text)
    # get text, strip hyperlinks, tags, and sources
    text = art.find(".//x:text", namespaces=ns).text
    text = re.sub(r"\[\[.*?\|(.*?)\]\]", "\\1", text, flags=re.DOTALL)
    text = re.sub("{{.*?}}", "", text, flags=re.DOTALL)
    text = text.strip()

    return dict(headline=title,
                date=date,
                author=author,
                externalid=id,
                url=url,
                text=text,
                medium="Wikinews")


def date_of_unit(self, doc):
     # find element like '<span id="publishDate" class="value-title" title="2004-11-15">'
     # and extract "title".
     return doc.cssselect('#publishDate')[0].get('title')

def scrape_wikinews(conn, project, articleset, category):
    """
    Scrape wikinews articles from the given category
    @param conn: The AmcatAPI object
    @param articleset: The target articleset ID
    @param category: The wikinews category name
    """
    url = "http://en.wikinews.org/wiki/Category:{}".format(category)
    for page in get_pages(url):
        arts = [get_article(a) for a in get_articles(page)]
        print("Adding {} articles to set {}:{}".format(len(arts), project, articleset))
        conn.create_articles(project=project, articleset=articleset,
                            json_data=arts)


if __name__ == '__main__':
    from amcatclient import AmcatAPI
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='The AmCAT host to connect to, '
                        'e.g. http://amcat.vu.nl')
    parser.add_argument('project', help='Project ID to add the articles to')
    parser.add_argument('category', help='Wikinews category to scrape')
    parser.add_argument('--username', help='Username for AmCAT login')
    parser.add_argument('--password', help='Password for AmCAT login')
    args = parser.parse_args()

    conn = AmcatAPI(args.host, args.username, args.password)
    category = "Iraq"
    articleset = conn.create_set(project=args.project,
                                 name="Wikinews articles {}".format(category),
                                 provenance="Scraped from wikinews on {}"
                                 .format(datetime.datetime.now().isoformat()))
    scrape_wikinews(conn, args.project, articleset['id'], category)
