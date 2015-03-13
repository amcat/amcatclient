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
Demo scraper for AmCAT

Scrapes all State of the Union addresses and uploads them into AmCAT.

Requirements:
- requests (can be installed using pip)
- lxml (can be installed using pip)
- amcatclient (this repository)

An English locale is needed to parse the dates, if the locale is not found
you can install it, e.g. on ubuntu: sudo locale-gen en_US.utf8
"""

# Import modules to get and parse HTML pages
import requests
from lxml import html

# Since we need to parse an English-language date (December 3, 2002),
# set the locale to english. You can skip this step on an English-language OS
import datetime
import locale
locale.setlocale(locale.LC_ALL, "en_US.utf8")


# Import amcatclient
from amcatclient import AmcatAPI

# Connect to AmCAT.
# Note: if you create a .amcatauth file in your home dir, there is no
#       need to specify username and password.
conn = AmcatAPI("http://amcat.vu.nl", "<username>","<password>")

# Create a new articleset to add the articles to.
# You can also just set 'setid' to add to an existing set
PROJECT_ID = 1
aset = conn.create_set(project=PROJECT_ID, name="State of the Union",
                       provenance="Scraped from http://www.presidency.ucsb.edu/sou.php")
setid = aset["id"]


# Get the main page and iterate over all links in a 'doclist'
page = requests.get('http://www.presidency.ucsb.edu/sou.php')
tree = html.fromstring(page.text)
for a in tree.cssselect("td.doclist a"):

    # Skip empty links and the 'jump to menu' link
    if not a.text_content().strip(): continue
    if a.text_content().strip() == "jump to menu": continue

    # Get the child page - this is a single state of the union
    page = requests.get(a.get('href'))
    tree = html.fromstring(page.text)

    # Get the date and parse it
    date = tree.cssselect(".docdate")[0].text_content()
    date = datetime.datetime.strptime(date, "%B %d, %Y")

    # Get the title, which starts with <president>:
    title = tree.cssselect("title")[0].text_content()
    president = title.split(":")[0]

    # Get all paragraphs in the displaytext and join together
    ps = tree.cssselect(".displaytext p")
    text = "\n\n".join(p.text_content() for p in ps)

    # Build the article dictionary and add it to AmCAT
    art = {"headline": president,
           "byline": title,
           "medium" : "Speeches",
           "text" : text,
           "date" : date.isoformat()
    }
    articles = conn.create_articles(project=1, articleset=setid, json_data=[art])
