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

import requests, json
import logging
import os, os.path, csv

log = logging.getLogger(__name__)

class URL:
    articleset = 'projects/{project}/articlesets/'
    article = articleset + '{articleset}/articles/'
    get_token = 'get_token'

AUTH_FILE = "~/.amcatauth"
    
class APIError(EnvironmentError):
    def __init__(self, http_status, message, url, response, description=None, details=None):
        super(APIError, self).__init__(http_status, message, url)
        self.http_status = http_status
        self.url = url
        self.response = response
        self.description = description
        self.details = details

def check(response, expected_status=200, url=None, json=True):
    """
    Check whether the status code of the response equals expected_status and raise an APIError otherwise.
    @param url: the url that was used to get the response (for error messages). Defaults to response.url
    @param json: if True, return r.json(), otherwise return r.text
    """
    if response.status_code != expected_status:
        if url is None: url = response.url
            
        try:
            err = response.json()
        except:
            # couldn't get json, so raise generic error
            msg = ("Request {url!r} returned code {response.status_code}, expected {expected_status}:\n{response.text}"
                   .format(**locals()))
            raise APIError(response.status_code, msg, url, response.text)
        else:
            if not all(x in err for x in ("status", "message", "description", "details")):
                msg = ("Request {url!r} returned code {response.status_code}, expected {expected_status}:\n{response.text}"
                       .format(**locals()))
                raise APIError(response.status_code, msg, url, response.text)    
            raise APIError(err["status"],  err['message'], url, err, err["description"], err["details"])
    if json:
        try:
            return response.json()
        except:
            raise Exception("Cannot decode json; text={response.text!r}".format(**locals()))
    else:
        return response.text
        
class AmcatAPI(object):
    def __init__(self, host, user=None, password=None, token=None):
        self.host = host
        if token is None: token = self.get_token(user, password)
        self.token = token

    def _get_auth(self, user=None, password=None):
        """
        Get the authentication info for the current user, from
        1) a ~/.amcatauth file, which should be a csv containing host, username, password entries
        2) the AMCAT_USER (or USER) and AMCAT_PASSWORD environment variables
        """
        fn = os.path.expanduser(AUTH_FILE)
        if os.path.exists(fn):
            for i, line in enumerate(csv.reader(open(fn))):
                if len(line) != 3:
                    log.warn("Cannot parse line {i} in {fn}".format(**locals()))
                    continue
                hostname, username, pwd = line
                if hostname in ("", "*", self.host) and (user is None or username == user):
                    return (username, pwd)
        if user is None:
            user = os.environ.get("AMCAT_USER", os.environ.get("USER"))
        if password is None:
            password = os.environ.get("AMCAT_PASSWORD")
        if user is None or password is None:
            raise Exception("No authentication info for {user}@{self.host} from {fn} or AMCAT_USER / AMCAT_PASSWORD variables"
                            .format(**locals()))
        return user, password
                           
                        
    def get_token(self, user=None, password=None):
        if user is None or password is None:
            user, password = self._get_auth()
        url = "{self.host}/api/v4/{url}".format(url=URL.get_token, **locals())
        r = requests.post(url, data={'username' : user, 'password' : password})
        return check(r)['token']
        
    def request(self, url, method="get", format="json", data=None, expected_status=None, headers=None, **options):
        """
        Make an HTTP request to the given relative URL with the host, user, and password information
        Returns the deserialized json if successful, and raises an exception otherwise
        """
        if expected_status is None:
            expected_status = dict(get=200, post=201)[method]
        url = "{self.host}/api/v4/{url}".format(**locals())
        options = dict({'format' : format}, **options)
        
        _headers = {"Authentication" : "Token: {self.token}".format(**locals())}
        if headers: _headers.update(headers)
        
        r = requests.request(method, url, data=data, params=options, headers=_headers)
        log.info("HTTP {method} {url} (options={options!r}, data={data!r}, headers={_headers}) -> {r.status_code}"
                 .format(**locals()))
        return check(r)
        
    def list_sets(self, project, **filters):
        """List the articlesets in a project"""
        url = URL.articleset.format(**locals())
        return self.request(url, **filters)

    def list_articles(self, project, articleset, **filters):
        """List the articles in a set"""
        url = URL.article.format(**locals())
        return self.request(url, **filters)
    
    def create_set(self, project, json_data=None, **options):
        """Create a new article set. Provide the needed arguments using the post_data or with key-value pairs"""
        url = URL.articleset.format(**locals())
        if json_data is None:
            # form encoded request
            return self.request(url, method="post", data=options)
        else:
            if not isinstance(json_data, (str, unicode)):
                json_data = json.dumps(json_data)
            headers = {'content-type': 'application/json'}
            return self.request(url, method='post', data=json_data, headers=headers)

    def create_articles(self, project, articleset, json_data=None, **options):
        """Create one or more articles in the set. Provide the needed arguments using the json_data or with key-value pairs

        json_data can be a dictionary or list of dictionaries. Each dict can contain a 'children' attribute which
        is another list of dictionaries. 
        """
        url = URL.article.format(**locals())
        if json_data is None: #TODO duplicated from create_set, move into requests (or separate post method?)
            # form encoded request
            return self.request(url, method="post", data=options)
        else:
            if not isinstance(json_data, (str, unicode)):
                json_data = json.dumps(json_data)
            headers = {'content-type': 'application/json'}
            return self.request(url, method='post', data=json_data, headers=headers)

        
if __name__ == '__main__':
    import argparse, sys, pydoc
    logging.basicConfig(level=logging.INFO)
    
    actions = {}
    for name in dir(AmcatAPI):
        if name.startswith("_"): continue
        fn = getattr(AmcatAPI, name)
        actions[name] = fn.__doc__
    epilog = "Possible actions (use api.py help <action> for help on the chosen action):\n%s" % ("\n".join("  {name}: {desc}".format(**locals()) for (name, desc) in actions.items()))

    parser = argparse.ArgumentParser(description=__doc__, epilog=epilog, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('host')
    parser.add_argument('username')
    parser.add_argument('password')
    parser.add_argument('action', help="The action to run. Valid options: help, list_sets. Use help <action> to get help op the chosen action")
    parser.add_argument('argument', help="Additional arguments for the action. User key=value to specify keyword arguments. Actions using post_data can be given using json encoded string or by pointing to a file using post_data=@filename.", nargs="*")
    opts = parser.parse_args()
    
    if opts.action == "help":
        if opts.argument:
            action = opts.argument[0]
            fn = getattr(AmcatAPI, action)
            print(pydoc.render_doc(fn, "Help on %s"))
        else:
            parser.print_help()
    else:
        api = AmcatAPI(opts.host, opts.username, opts.password)
        action = getattr(api, opts.action)
        args, kargs = [], {}
        for arg in opts.argument:
            if "=" in arg:
                k, v = arg.split("=", 1)
                if v.startswith("@"):
                    # get post data from (json-encoded) file
                    v = open(v[1:]).read()
                kargs[k] = v
            else:
                args.append(arg)

        try:
            result = action(*args, **kargs)
        except TypeError,e :
            print("TypeError on calling {action.__name__}: {e}\n".format(**locals()))
            print(pydoc.render_doc(action, "Help on %s"), file=sys.stderr)
            sys.exit(1)
                
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        print()
