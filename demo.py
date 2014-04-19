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
