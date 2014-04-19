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
Demo script for reading articles using the AmCAT API

Reads all articles from a set and counts the words in the article
"""

import argparse
import collections
import re

from amcatclient import AmcatAPI

# Connect to AmCAT
parser = argparse.ArgumentParser()
parser.add_argument('host', help='The AmCAT host to connect to, '
                    'e.g. http://amcat.vu.nl')
parser.add_argument('project', help='The project to count words in')
parser.add_argument('articleset', help='The article set to count words in')
parser.add_argument('--username', help='Username for AmCAT login')
parser.add_argument('--password', help='Password for AmCAT login')
args = parser.parse_args()

conn = AmcatAPI(args.host, args.username, args.password)

# Iterate over the articles, count all words
counts = collections.Counter()
for a in conn.list_articles(args.project, args.articleset):
    # get words by splitting lowercased text on non-word characters
    text = a['text'].lower()
    words = re.split("\W+", text)
    counts.update(words)

# delete all words with <= 3 characters
for word in counts.keys():
    if len(word) <= 3:
        del counts[word]

# print most common words
for word, n in counts.most_common(n=20):
    print("{n:5} {word}".format(**locals()))
