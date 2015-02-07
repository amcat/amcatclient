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
import logging
from lxml import html, etree
logging.basicConfig(level=logging.INFO)

######################################################################
###       Functions specific to reading/parsing wiki news          ###
######################################################################

def get_pages(url):
    """
    Return the 'pages' from the starting url
    Technically, look for the 'next 50' link, yield and download it,  repeat
    """
    while True:
        yield url
        doc = html.parse(url).find("body")
        links = [a for a in doc.findall(".//a") if a.text and a.text.startswith("next ")]
        if not links:
            break
        url = urljoin(url, links[0].get('href'))

def get_article_urls(url):
    """
    Return the articles from a page
    Technically, look for a div with class mw-search-result-heading
    and get the first link from this div
    """
    doc = html.parse(url).getroot()
    for div in doc.cssselect("div.mw-search-result-heading"):
        href = div.cssselect("a")[0].get('href')
        if ":" in href:
            continue # skip Category: links
        href = urljoin(url, href)
        yield href

def export_url(url):
    """
    Get the 'Special:Export' XML version url of an article
    """
    page = url.split("/")[-1]
    return ("http://en.wikinews.org/w/index.php?title=Special:Export"
            "&action=submit&pages={}".format(page))


def get_articles(urls):
    for url in urls:
        try:
            yield get_article(url)
        except:
            logging.exception("Error on scraping {}".format(url))


def get_article(url):
    """
    Return a single article as a 'amcat-ready' dict
    Uses the 'export' function of wikinews to get an xml article
    """
    a = html.parse(url).getroot()
    title = a.cssselect(".firstHeading")[0].text_content()
    date = a.cssselect(".published")[0].text_content()
    date = datetime.datetime.strptime(date, "%A, %B %d, %Y").isoformat()
    paras = a.cssselect("#mw-content-text p")
    paras = paras[1:] # skip first paragraph, which contains date
    text = "\n\n".join(p.text_content().strip() for p in paras)

    return dict(headline=title,
                date=date,
                url=url,
                text=text,
                medium="Wikinews")


def date_of_unit(self, doc):
     # find element like '<span id="publishDate" class="value-title" title="2004-11-15">'
     # and extract "title".
     return doc.cssselect('#publishDate')[0].get('title')

######################################################################
###       AmCAT functionality: connect to API and add articles     ###
######################################################################

def scrape_wikinews(conn, project, articleset, query):
    """
    Scrape wikinews articles from the given query
    @param conn: The AmcatAPI object
    @param articleset: The target articleset ID
    @param category: The wikinews category name
    """
    url = "http://en.wikinews.org/w/index.php?search={}&limit=50".format(query)
    logging.info(url)
    for page in get_pages(url):
        urls = get_article_urls(page)
        arts = list(get_articles(urls))
        logging.info("Adding {} articles to set {}:{}"
                     .format(len(arts), project, articleset))
        conn.create_articles(project=project, articleset=articleset,
                            json_data=arts)


if __name__ == '__main__':
    from amcatclient import AmcatAPI
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='The AmCAT host to connect to, '
                        'e.g. http://amcat.vu.nl')
    parser.add_argument('project', help='Project ID to add the articles to')
    parser.add_argument('query', help='Wikinews query for scraping')
    parser.add_argument('--username', help='Username for AmCAT login')
    parser.add_argument('--password', help='Password for AmCAT login')
    args = parser.parse_args()

    conn = AmcatAPI(args.host, args.username, args.password)
    category = "Iraq"
    articleset = conn.create_set(project=args.project,
                                 name="Wikinews articles for {}".format(args.query),
                                 provenance="Scraped from wikinews on {}"
                                 .format(datetime.datetime.now().isoformat()))
    scrape_wikinews(conn, args.project, articleset['id'], args.query)
