from api import AmcatAPI
import sys
 
host, username, password = sys.argv[1:]
 
api = AmcatAPI(host, username, password)
 
articles_json = [
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
articles = api.create_articles(project=1, articleset=aset["id"], json_data=articles_json)
print "Added {n} articles to set {setid}".format(n=len(articles), setid=aset["id"])
