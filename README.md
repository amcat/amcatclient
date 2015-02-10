amcatclient
===========

Client code for interfacing with the AmCAT API. 

Installing
----------

You can install amcatclient directly from github using pip: 

```{sh}
pip install git+git://github.com/amcat/amcatclient
```

(Note that this requires that you either use sudo or a virtual environment)

You can also copy file [amcatclient.py](amcatclient/amcatclient.py), which you can download or clone using git. 
Since his is licensed with the permissive MIT license, feel free to include this file in your own projects, whether open source or not.

Usage
-----

```
from amcatclient import AmcatAPI
conn = AmcatAPI("http://amcat.vu.nl", username, password)
```

It is advised to create a `.amcatauth` file in your home directory, which should contain the hostname, username, password for the server(s) you want to use (comma separated, one server per line). In that case, you can omit the authentication info:


```
from amcatclient import AmcatAPI
conn = AmcatAPI("http://amcat.vu.nl")
```

See the [source code](amcatclient.py) for the API methods (sorry!). [demo_wordcount.py](demo_wordcount.py) shows how to use the client to retrieve a set of articles and count the words. [demo_scraper.py](demo_scraper.py) shows a simple scraper that adds all State of the Union speeches to AmCAT. 

