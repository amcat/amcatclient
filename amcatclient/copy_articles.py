###########################################################################
#          (C) Vrije Universiteit, Amsterdam (the Netherlands)            #
#                                                                         #
# This file is part of AmCAT - The Amsterdam Content Analysis Toolkit     #
#                                                                         #
# AmCAT is free software: you can redistribute it and/or modify it under  #
# the terms of the GNU Lesser General Public License as published by the  #
# Free Software Foundation, either version 3 of the License, or (at your  #
# option) any later version.                                              #
#                                                                         #
# AmCAT is distributed in the hope that it will be useful, but WITHOUT    #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or   #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public     #
# License for more details.                                               #
#                                                                         #
# You should have received a copy of the GNU Lesser General Public        #
# License along with AmCAT.  If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

"""
Copy articles to a different amcat server using the API

Limitations: does not copy UUID or parent/child relations
"""

import argparse
import requests
import logging
import itertools

from amcatclient import AmcatAPI



SET_ARGS = ["name", "provenance"]
ART_ARGS = ["metastring", "byline", "uuid", "author", "headline", "text",
            "section", "url", "length", "addressee", "externalid",
            "insertdate", "date", "pagenr", "medium", "parent"]


def create_set(src_api, src_project, src_set, trg_api, trg_project):
    s = src_api.get_set(src_project, src_set)
    s = {k: v for (k, v) in s.items() if k in SET_ARGS}

    provenance = "Copied from {src_api.host} project {src_project} set {src_set}".format(**locals())
    if s.get('provenance'):
        s['provenance'] = "\n".join([s['provenance'], provenance])
    else:
        s['provenance'] = provenance

    result = trg.create_set(trg_project, s)
    logging.info("Created set {id}:{name} in project {project}"
                 .format(**result))
    return result["id"]


def copy_articles(src_api, src_project, src_set,
                  trg_api, trg_project, trg_set=None,
                  batch_size=100, from_page=1):
    if trg_set is None:
        trg_set = create_set(src_api, src_project, src_set, trg_api, trg_project)
    articles = src_api.list_articles(src_project, src_set, page=from_page, page_size=batch_size, order_by="parent", text=True)
    for i in itertools.count(from_page):
        batch = list(itertools.islice(articles, batch_size))
        if not batch:
            logging.info("Done")
            break
        logging.info("Copying batch {i}: {n} articles"
                     .format(n=len(batch), **locals()))

        def convert(a):
            a = {k: v for (k, v) in a.items() if k in ART_ARGS}
            if not a['text']: a['text'] = "-"
            if not a['headline']: a['headline']="-"
            return a
        batch = [convert(a) for a in batch]

        trg_api.create_articles(trg_project, trg_set, batch)

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
                        type=int, default=100)
    parser.add_argument("--from-page", "-p", help='Start from page (batch)',
                        type=int, default=1)


    args = parser.parse_args()

    fmt = '[%(asctime)s %(levelname)s %(name)s] %(message)s'
    logging.basicConfig(format=fmt, level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)

    src = AmcatAPI(args.source_url)
    trg = AmcatAPI(args.target_url)


    copy_articles(src, args.source_project, args.source_set,
                  trg, args.target_project, args.target_set,
                  args.batch_size, args.from_page)
