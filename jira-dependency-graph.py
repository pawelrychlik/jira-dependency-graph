#!/usr/bin/env python
import optparse
from itertools import chain
import json
from urllib import quote_plus

from restkit import Resource, BasicAuth, request

# Using REST is pretty simple. The vast majority of this code is about the "other stuff": dealing with
# command line options, formatting graphviz, calling Google Charts, etc. The actual JIRA REST-specific code
# is only about 5 lines.

GOOGLE_CHART_URL = 'http://chart.apis.google.com/chart?'

def fetcher_factory(url, auth):
    """ This factory will create the actual method used to fetch issues from JIRA. This is really just a closure that saves us having
        to pass a bunch of parameters all over the place all the time. """
    def get_issue(key):
        """ Given an issue key (i.e. JRA-9) return the JSON representation of it. This is the only place where we deal
            with JIRA's REST API. """
        print('Fetching ' + key)
        # we need to expand subtasks and links since that's what we care about here.
        resource = Resource(url + ('/rest/api/latest/issue/%s' % key), filters=[auth])
        response = resource.get(headers = {'Content-Type' : 'application/json'})
        if response.status_int == 200:
            # Not all resources will return 200 on success. There are other success status codes. Like 204. We've read
            # the documentation for though and know what to expect here.
            issue = json.loads(response.body_string())
            return issue
        else:
            return None
    return get_issue

def build_graph_data(start_issue_key, get_issue):
    """ Given a starting image key and the issue-fetching function build up the GraphViz data representing relationships
        between issues. This will consider both subtasks and issue links.
    """
    def get_key(issue):
        return issue['key']

    # since the graph can be cyclic we need to prevent infinite recursion
    seen = []

    def walk(issue_key, graph):
        """ issue is the JSON representation of the issue """
        issue = get_issue(issue_key)
        seen.append(issue_key)
        children = []
        fields = issue['fields']
        if fields.has_key('subtasks'):
            for other_issue in fields['subtasks']:
                node = '"%s"->"%s"[color=blue][penwidth=2.0]' % (issue_key, get_key(other_issue))
                graph.append(node)
                children.append(get_key(other_issue))
        if fields.has_key('issuelinks'):
            for other_link in fields['issuelinks']:
                # Only add graphviz data for outbound links since that will also draw the corresponding inbound link
                if other_link.has_key('outwardIssue'):
                    other_issue = other_link['outwardIssue']
                    other_issue_key = get_key(other_issue)
                    link_type = other_link['type']['outward']
                    print('issue = ' + other_issue_key + ' link type = ' + link_type)
                    node = '"%s"->"%s"[arrowhead=empty][label="%s"]' % (issue_key, other_issue_key, quote_plus(link_type))
                    graph.append(node)
                    children.append(get_key(other_issue))
                if other_link.has_key('inwardIssue'):
                    other_issue = other_link['inwardIssue']
                    other_issue_key = get_key(other_issue)
                    link_type = other_link['type']['inward']
                    print('issue = ' + other_issue_key + ' link type = ' + link_type)
                    node = '"%s"->"%s"[arrowhead=empty][label="%s"]' % (other_issue_key, issue_key, quote_plus(link_type))
                    graph.append(node)
                    children.append(get_key(other_issue))
        # now construct graph data for all subtasks and links of this issue
        for child in (x for x in children if x not in seen):
            walk(child, graph)
        return graph

    graph = walk(start_issue_key, [])
    return graph

def create_graph_image(graph_data, image_file):
    """ Given a formatted blob of graphviz chart data[1], make the actual request to Google
        and store the resulting image to disk.

        [1]: http://code.google.com/apis/chart/docs/gallery/graphviz.html
    """
    chart_url = GOOGLE_CHART_URL + 'cht=gv&chl=digraph{%s}' % ';'.join(graph_data)

    print('Google Chart request:')
    print(chart_url)

    g = request(chart_url)

    print('Writing to ' + image_file)
    image = open(image_file, 'w+')
    image.write(g.body_stream().read())
    image.close()
    return image_file

def parse_args():
    parser = optparse.OptionParser()
    parser.add_option('-u', '--user', dest='user', default='admin', help='Username to access JIRA')
    parser.add_option('-p', '--password', dest='password', default='admin', help='Password to access JIRA')
    parser.add_option('-j', '--jira', dest='jira_url', default='http://jira.example.com', help='JIRA Base URL')
    parser.add_option('-f', '--file', dest='image_file', default='issue_graph.png', help='Filename to write image to')

    return parser.parse_args()

if __name__ == '__main__':
    (options, args) = parse_args()

    # Basic Auth is usually easier for scripts like this to deal with than Cookies.
    auth = BasicAuth(options.user, options.password)
    issue_fetcher = fetcher_factory(options.jira_url, auth)

    if len(args) != 1:
        print('Must specify exactly one issue key. (e.g. JRADEV-1107, JRADEV-1391)')
        import sys; sys.exit(1)
    start_issue_key = args[0]

    graph = build_graph_data(start_issue_key, issue_fetcher)
    create_graph_image(graph, options.image_file)

