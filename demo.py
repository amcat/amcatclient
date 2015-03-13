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

import argparse
from amcatclient import AmcatAPI

# Connect to AmCAT
parser = argparse.ArgumentParser()
parser.add_argument('host', help='The AmCAT host to connect to, '
                    'e.g. http://amcat.vu.nl')
parser.add_argument('--username', help='Username for AmCAT login')
parser.add_argument('--password', help='Password for AmCAT login')
args = parser.parse_args()

conn = AmcatAPI(args.host, args.username, args.password)

articles = [
    {"headline" : "test headline3",
     "medium" : "test medium",
     "text" : "test text",
     "date" : "2013-01-01"
     },
    {"headline" : "test headline4",
     "medium" : "test medium",
     "text" : "test text",
     "date" : "2013-01-01"
     }
    ]

aset = api.create_set(project=1, name="Testset", provenance="test data")
articles = api.create_articles(project=1, articleset=aset["id"],
                               json_data=articles)
print "Added {n} articles to set {setid}".format(n=len(articles),
                                                 setid=aset["id"])
