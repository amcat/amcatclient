"""
Copy articles to a different amcat server using the API

Limitations: does not copy UUID or parent/child relations
"""

import argparse
import requests
import logging
import itertools

from amcatclient import api



SET_ARGS = ["name", "provenance"]
ART_ARGS = ["metastring", "byline", "uuid", "author", "headline", "text",
            "section", "url", "length", "addressee", "externalid",
            "insertdate", "date", "pagenr"]

class Copier(object):
    def __init__(self, src, trg, src_project, src_set, trg_project, trg_set):
        self.src = src
        self.trg = trg
        self.src_project = src_project
        self.src_set = src_set
        self.trg_project = trg_project
        self.trg_set = trg_set
        self.media = {}

    @property
    def target_set(self):
        if self.trg_set is None:
            s = src.get_set(self.src_project, self.src_set)
            s = {k: v for (k, v) in s.iteritems() if k in SET_ARGS}
            s['favourite'] = True

            result = trg.create_set(self.trg_project, s)
            logging.info("Created set {id}:{name} in project {project}"
                         .format(**result))
            self.trg_set = result["id"]
        return self.trg_set

    def get_medium(self, mid):
        if mid not in self.media:
            self.get_media([mid])
        return self.media[mid]

    def get_media(self, mids):
        mids = set(mids) - set(self.media)
        if mids:
            for medium in self.src.get_media(mids)['results']:
                self.media[medium['id']] = medium['name']

    def convert(self, article):
        result = {k: v for (k,v) in article.iteritems() if k in ART_ARGS}
        result['medium'] = self.media[article['medium']]
        result['project'] = self.trg_project
        return result

    def copy(self, batch_size):
        for page in itertools.count(1):
            l = self.src.list_articles(self.src_project, self.src_set,
                                       page=page, page_size=batch_size)
            logging.info("Copying page {page} / {pages}"
                         .format(**l))

            mediumids = {a['medium'] for a in l['results']}
            self.get_media(mediumids)

            articles = [self.convert(a) for a in l['results']]
            self.trg.create_articles(self.trg_project, self.target_set, articles)
            if page == int(l['pages']):
                return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(epilog=__doc__)
    parser.add_argument("source_url", help='URL of the source '
                        '(e.g. "http://amcat-dev.labs.vu.nl")')
    parser.add_argument("target_url", help='URL of the target '
                        '(e.g. "http://amcat.vu.nl")')
    parser.add_argument("source_project", help='Article set ID in the source',
                        type=int)
    parser.add_argument("source_set", help='Article set ID in the source',
                        type=int)
    parser.add_argument("target_project", help='Project ID in the target',
                        type=int)
    parser.add_argument("--target-set", "-s", help='Article set ID in the '
                        'target (if omitted, a new set will be created',
                        type=int)
    parser.add_argument("--batch-size", "-b", help='Batch size for copying',
                        type=int, default=10)

    args = parser.parse_args()

    fmt = '[%(asctime)s %(levelname)s %(name)s] %(message)s'
    logging.basicConfig(format=fmt, level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    src = api.AmcatAPI(args.source_url)
    trg = api.AmcatAPI(args.target_url)

    Copier(src, trg, args.source_project, args.source_set,
           args.target_project, args.target_set).copy(args.batch_size)
