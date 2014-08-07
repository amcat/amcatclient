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
from __future__ import unicode_literals, print_function, absolute_import

"""
Utility module for accessing the AmCAT API.

This module is designed to be used as an independent module, so you can copy
this file into your project. For that reason, this module is also licensed
under the GNU Lesser GPL rather than the Affero GPL, so feel free to use it
in non-GPL programs.
"""

import requests
import json
import logging
import os
import os.path
import csv
import itertools

log = logging.getLogger(__name__)

def serialize(obj):
    """JSON serializer that accepts datetime & date"""
    from datetime import datetime, date
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

class URL:
    articlesets = 'projects/{project}/articlesets/'
    articleset = articlesets + '{articleset}/'
    article = articleset + 'articles/'
    xtas = article + '{article}/xtas/{method}/'
    get_token = 'get_token'
    media = 'medium'

AUTH_FILE = os.path.join("~", ".amcatauth")


class APIError(EnvironmentError):

    def __init__(self, http_status, message, url,
                 response, description=None, details=None):
        super(APIError, self).__init__(http_status, message, url)
        self.http_status = http_status
        self.url = url
        self.response = response
        self.description = description
        self.details = details


def check(response, expected_status=200, url=None, json=True):
    """
    Check whether the status code of the response equals expected_status and
    raise an APIError otherwise.
    @param url: The url of the response (for error messages).
                Defaults to response.url
    @param json: if True, return r.json(), otherwise return r.text
    """
    if response.status_code != expected_status:
        if url is None:
            url = response.url

        try:
            err = response.json()
        except:
            # couldn't get json, so raise generic error
            msg = ("Request {url!r} returned code {response.status_code}, "
                   "expected {expected_status}:\n{response.text}"
                   .format(**locals()))
            raise APIError(response.status_code, msg, url, response.text)
        else:
            if not all(x in err for x in ("status", "message",
                                          "description", "details")):
                msg = ("Request {url!r} returned code {response.status_code},"
                       " expected {expected_status}:\n{response.text}"
                       .format(**locals()))
                raise APIError(response.status_code, msg, url, response.text)
            raise APIError(err["status"], err['message'], url,
                           err, err["description"], err["details"])
    if json:
        try:
            return response.json()
        except:
            raise Exception("Cannot decode json; text={response.text!r}"
                            .format(**locals()))
    else:
        return response.text


class AmcatAPI(object):

    def __init__(self, host, user=None, password=None, token=None):
        self.host = host
        if token is None:
            token = self.get_token(user, password)
        self.token = token

    def _get_auth(self, user=None, password=None):
        """
        Get the authentication info for the current user, from
        1) a ~/.amcatauth file, which should be a csv file
          containing host, username, password entries
        2) the AMCAT_USER (or USER) and AMCAT_PASSWORD environment variables
        """
        fn = os.path.expanduser(AUTH_FILE)
        if os.path.exists(fn):
            for i, line in enumerate(csv.reader(open(fn))):
                if len(line) != 3:
                    log.warn(
                        "Cannot parse line {i} in {fn}".format(**locals()))
                    continue
                hostname, username, pwd = line
                if (hostname in ("", "*", self.host)
                    and (user is None or username == user)):
                    return (username, pwd)
        if user is None:
            user = os.environ.get("AMCAT_USER", os.environ.get("USER"))
        if password is None:
            password = os.environ.get("AMCAT_PASSWORD")
        if user is None or password is None:
            raise Exception("No authentication info for {user}@{self.host} "
                            "from {fn} or AMCAT_USER / AMCAT_PASSWORD "
                            "variables".format(**locals()))
        return user, password

    def get_token(self, user=None, password=None):
        if user is None or password is None:
            user, password = self._get_auth()
        url = "{self.host}/api/v4/{url}".format(url=URL.get_token, **locals())
        r = requests.post(url, data={'username': user, 'password': password})
        return check(r)['token']

    def request(self, url, method="get", format="json", data=None,
                expected_status=None, headers=None, **options):
        """
        Make an HTTP request to the given relative URL with the host,
        user, and password information. Returns the deserialized json
        if successful, and raises an exception otherwise
        """
        if expected_status is None:
            expected_status = dict(get=200, post=201)[method]
        url = "{self.host}/api/v4/{url}".format(**locals())
        options = dict({'format': format}, **options)

        _headers = {"Authorization": "Token {self.token}".format(**locals())}
        if headers:
            _headers.update(headers)
        r = requests.request(
            method, url, data=data, params=options, headers=_headers)
        log.debug("HTTP {method} {url} (options={options!r}, "
                 "data={data!r}, headers={_headers}) -> {r.status_code}"
                 .format(**locals()))
        return check(r, expected_status=expected_status)

    def get_pages(self, url, page=1, **filters):
        r = self.request(url)
        for page in itertools.count(page):
            r = self.request(url, page=page, **filters)
            log.debug("Got {url} page {page} / {pages}".format(url=url, **r))
            for row in r['results']:
                yield row
            if r['next'] is None:
                break

    def list_sets(self, project, **filters):
        """List the articlesets in a project"""
        url = URL.articlesets.format(**locals())
        return self.get_pages(url, **filters)

    def get_set(self, project, articleset, **filters):
        """List the articlesets in a project"""
        url = URL.articleset.format(**locals())
        return self.request(url, **filters)

    def list_articles(self, project, articleset, **filters):
        """List the articles in a set"""
        url = URL.article.format(**locals())
        return self.get_pages(url, **filters)

    def get_media(self, medium_ids):
        query = "&".join("pk={}".format(mid) for mid in medium_ids)
        url = "{}?{}".format(URL.media, query)
        return self.request(url, page_size=len(medium_ids))

    def create_set(self, project, json_data=None, **options):
        """
        Create a new article set. Provide the needed arguments using
        post_data or with key-value pairs
        """
        url = URL.articlesets.format(**locals())
        if json_data is None:
            # form encoded request
            return self.request(url, method="post", data=options)
        else:
            if not isinstance(json_data, (str, unicode)):
                json_data = json.dumps(json_data,default = serialize)
            headers = {'content-type': 'application/json'}
            return self.request(
                url, method='post', data=json_data, headers=headers)

    def create_articles(self, project, articleset, json_data=None, **options):
        """
        Create one or more articles in the set. Provide the needed arguments
        using the json_data or with key-value pairs
        @param json_data: A dictionary or list of dictionaries. Each dict
                          can contain a 'children' attribute which
                          is another list of dictionaries.
        """
        url = URL.article.format(**locals())
        # TODO duplicated from create_set, move into requests
        # (or separate post method?)
        if json_data is None:
            # form encoded request
            return self.request(url, method="post", data=options)
        else:
            if not isinstance(json_data, (str, unicode)):
                json_data = json.dumps(json_data,default = serialize)
            headers = {'content-type': 'application/json'}
            return self.request(
                url, method='post', data=json_data, headers=headers)

    def get_parse(self, project, articleset, article, method):
        url = URL.xtas.format(**locals())
        return self.request(url)