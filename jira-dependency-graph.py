#!/usr/bin/env python

from __future__ import print_function

import argparse
import getpass
import sys
import textwrap

import requests
from functools import reduce

GOOGLE_CHART_URL = 'https://chart.apis.google.com/chart'
MAX_SUMMARY_LENGTH = 30


def log(*args):
    print(*args, file=sys.stderr)


class JiraSearch(object):
    """ This factory will create the actual method used to fetch issues from JIRA. This is really just a closure that
        saves us having to pass a bunch of parameters all over the place all the time. """

    __base_url = None

    def __init__(self, url, auth, no_verify_ssl):
        self.__base_url = url
        self.url = url + '/rest/api/latest'
        self.auth = auth
        self.no_verify_ssl = no_verify_ssl
        self.fields = ','.join(['key', 'summary', 'status', 'description', 'issuetype', 'issuelinks', 'subtasks'])

    def get(self, uri, params={}):
        headers = {'Content-Type' : 'application/json'}
        url = self.url + uri

        if isinstance(self.auth, str):
            return requests.get(url, params=params, cookies={'JSESSIONID': self.auth}, headers=headers, verify=self.no_verify_ssl)
        else:
            return requests.get(url, params=params, auth=self.auth, headers=headers, verify=(not self.no_verify_ssl))

    def get_issue(self, key):
        """ Given an issue key (i.e. JRA-9) return the JSON representation of it. This is the only place where we deal
            with JIRA's REST API. """
        log('Fetching ' + key)
        # we need to expand subtasks and links since that's what we care about here.
        response = self.get('/issue/%s' % key, params={'fields': self.fields})
        response.raise_for_status()
        return response.json()

    def query(self, query):
        log('Querying ' + query)
        response = self.get('/search', params={'jql': query, 'fields': self.fields})
        content = response.json()
        return content['issues']

    def list_ids(self, query):
        log('Querying ' + query)
        response = self.get('/search', params={'jql': query, 'fields': 'key', 'maxResults': 100})
        return [issue["key"] for issue in response.json()["issues"]]

    def get_issue_uri(self, issue_key):
        return self.__base_url + '/browse/' + issue_key


def build_graph_data(start_issue_key, jira, excludes, show_directions, directions, includes, issue_excludes,
                     ignore_closed, ignore_epic, ignore_subtasks, traverse, word_wrap):
    """ Given a starting image key and the issue-fetching function build up the GraphViz data representing relationships
        between issues. This will consider both subtasks and issue links.
    """
    def get_key(issue):
        return issue['key']

    def get_status_color(status_field):
        status = status_field['statusCategory']['name'].upper()
        if status == 'IN PROGRESS':
            return 'yellow'
        elif status == 'DONE':
            return 'green'
        return 'white'

    def create_node_text(issue_key, fields, islink=True):
        summary = fields['summary']
        status = fields['status']

        if word_wrap == True:
            if len(summary) > MAX_SUMMARY_LENGTH:
                # split the summary into multiple lines adding a \n to each line
                summary = textwrap.fill(fields['summary'], MAX_SUMMARY_LENGTH)
        else:
            # truncate long labels with "...", but only if the three dots are replacing more than two characters
            # -- otherwise the truncated label would be taking more space than the original.
            if len(summary) > MAX_SUMMARY_LENGTH + 2:
                summary = fields['summary'][:MAX_SUMMARY_LENGTH] + '...'
        summary = summary.replace('"', '\\"')
        # log('node ' + issue_key + ' status = ' + str(status))

        if islink:
            return '"{}\\n({})"'.format(issue_key, summary)
        return '"{}\\n({})" [href="{}", fillcolor="{}", style=filled]'.format(issue_key, summary, jira.get_issue_uri(issue_key), get_status_color(status))

    def process_link(fields, issue_key, link):
        if 'outwardIssue' in link:
            direction = 'outward'
        elif 'inwardIssue' in link:
            direction = 'inward'
        else:
            return

        if direction not in directions:
            return

        linked_issue = link[direction + 'Issue']
        linked_issue_key = get_key(linked_issue)

        if skip_issue(linked_issue_key, linked_issue['fields']):
            # logging present in skip_issue(), hence bare return here
            return

        if linked_issue_key in issue_excludes:
            log('Skipping ' + linked_issue_key + ' - explicitly excluded')
            return

        link_type = link['type'][direction]

        if ignore_closed:
            if ('inwardIssue' in link) and (link['inwardIssue']['fields']['status']['name'] in 'Closed'):
                log('Skipping ' + linked_issue_key + ' - linked key is Closed')
                return
            if ('outwardIssue' in link) and (link['outwardIssue']['fields']['status']['name'] in 'Closed'):
                log('Skipping ' + linked_issue_key + ' - linked key is Closed')
                return

        if includes not in linked_issue_key:
            return

        if link_type.strip() in excludes:
            return linked_issue_key, None

        arrow = ' => ' if direction == 'outward' else ' <= '
        log(issue_key + arrow + link_type + arrow + linked_issue_key)

        extra = ',color="red"' if link_type == "blocks" else ""

        if direction not in show_directions:
            node = None
        else:
            # log("Linked issue summary " + linked_issue['fields']['summary'])
            node = '{}->{}[label="{}"{}]'.format(
                create_node_text(issue_key, fields),
                create_node_text(linked_issue_key, linked_issue['fields']),
                link_type, extra)

        return linked_issue_key, node

    # since the graph can be cyclic we need to prevent infinite recursion
    seen = []

    def walk(issue_key, graph):
        """ issue is the JSON representation of the issue """
        issue = jira.get_issue(issue_key)
        children = []
        fields = issue['fields']
        seen.append(issue_key)

        if skip_issue(issue_key, fields):
            return graph

        graph.append(create_node_text(issue_key, fields, islink=False))

        if not ignore_subtasks:
            if fields['issuetype']['name'] == 'Epic' and not ignore_epic:
                issues = jira.query('"Epic Link" = "%s"' % issue_key)
                for subtask in issues:
                    subtask_key = get_key(subtask)
                    log(subtask_key + ' => references epic => ' + issue_key)
                    if not skip_issue(subtask_key, subtask['fields']):
                        node = '{}->{}[color=orange]'.format(
                            create_node_text(issue_key, fields),
                            create_node_text(subtask_key, subtask['fields']))
                        graph.append(node)
                        children.append(subtask_key)
            if 'subtasks' in fields and not ignore_subtasks:
                for subtask in fields['subtasks']:
                    subtask_key = get_key(subtask)
                    log(issue_key + ' => has subtask => ' + subtask_key)
                    node = '{}->{}[color=blue][label="subtask"]'.format (
                            create_node_text(issue_key, fields),
                            create_node_text(subtask_key, subtask['fields']))
                    graph.append(node)
                    children.append(subtask_key)

        if 'issuelinks' in fields:
            for other_link in fields['issuelinks']:
                result = process_link(fields, issue_key, other_link)
                if result is not None:
                    log('Appending ' + result[0])
                    children.append(result[0])
                    if result[1] is not None:
                        graph.append(result[1])
        # now construct graph data for all subtasks and links of this issue
        for child in (x for x in children if x not in seen):
            walk(child, graph)
        return graph

    def skip_issue(issue_key, fields):
        if ignore_closed and (fields['status']['name'] in 'Closed'):
            log('Skipping ' + issue_key + ' - it is Closed')
            return True
        if not traverse and ((project_prefix + '-') not in issue_key):
            log('Skipping ' + issue_key + ' - not traversing to a different project')
            return True
        return False

    project_prefix = start_issue_key.split('-', 1)[0]
    return walk(start_issue_key, [])


def create_graph_image(graph_data, image_file, node_shape):
    """ Given a formatted blob of graphviz chart data[1], make the actual request to Google
        and store the resulting image to disk.

        [1]: http://code.google.com/apis/chart/docs/gallery/graphviz.html
    """
    digraph = 'digraph{node [shape=' + node_shape +'];%s}' % ';'.join(graph_data)

    response = requests.post(GOOGLE_CHART_URL, data = {'cht':'gv', 'chl': digraph})

    with open(image_file, 'w+b') as image:
        print('Writing to ' + image_file)
        binary_format = bytearray(response.content)
        image.write(binary_format)
        image.close()

    return image_file


def print_graph(graph_data, node_shape):
    print('digraph{\nnode [shape=' + node_shape +'];\n\n%s\n}' % ';\n'.join(graph_data))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', dest='user', default=None, help='Username to access JIRA')
    parser.add_argument('-p', '--password', dest='password', default=None, help='Password to access JIRA')
    parser.add_argument('-c', '--cookie', dest='cookie', default=None, help='JSESSIONID session cookie value')
    parser.add_argument('-N', '--no-auth', dest='no_auth', action='store_true', default=False, help='Use no authentication')
    parser.add_argument('-j', '--jira', dest='jira_url', default='http://jira.example.com', help='JIRA Base URL (with protocol)')
    parser.add_argument('-f', '--file', dest='image_file', default='issue_graph.png', help='Filename to write image to')
    parser.add_argument('-l', '--local', action='store_true', default=False, help='Render graphviz code to stdout')
    parser.add_argument('-e', '--ignore-epic', action='store_true', default=False, help='Don''t follow an Epic into it''s children issues')
    parser.add_argument('-x', '--exclude-link', dest='excludes', default=[], action='append', help='Exclude link type(s)')
    parser.add_argument('-ic', '--ignore-closed', dest='closed', action='store_true', default=False, help='Ignore closed issues')
    parser.add_argument('-i', '--issue-include', dest='includes', default='', help='Include issue keys')
    parser.add_argument('-xi', '--issue-exclude', dest='issue_excludes', action='append', default=[], help='Exclude issue keys; can be repeated for multiple issues')
    parser.add_argument('-s', '--show-directions', dest='show_directions', default=['inward', 'outward'], help='which directions to show (inward, outward)')
    parser.add_argument('-d', '--directions', dest='directions', default=['inward', 'outward'], help='which directions to walk (inward, outward)')
    parser.add_argument('--jql', dest='jql_query', default=None, help='JQL search for issues (e.g. \'project = JRADEV\')')
    parser.add_argument('-ns', '--node-shape', dest='node_shape', default='box', help='which shape to use for nodes (circle, box, ellipse, etc)')
    parser.add_argument('-t', '--ignore-subtasks', action='store_true', default=False, help='Don''t include sub-tasks issues')
    parser.add_argument('-T', '--dont-traverse', dest='traverse', action='store_false', default=True, help='Do not traverse to other projects')
    parser.add_argument('-w', '--word-wrap', dest='word_wrap', default=False, action='store_true', help='Word wrap issue summaries instead of truncating them')
    parser.add_argument('--no-verify-ssl', dest='no_verify_ssl', default=False, action='store_true', help='Don\'t verify SSL certs for requests')
    parser.add_argument('issues', nargs='*', help='The issue key (e.g. JRADEV-1107, JRADEV-1391)')
    return parser.parse_args()


def filter_duplicates(lst):
    # Enumerate the list to restore order lately; reduce the sorted list; restore order
    def append_unique(acc, item):
        return acc if acc[-1][1] == item[1] else acc.append(item) or acc
    srt_enum = sorted(enumerate(lst), key=lambda i_val: i_val[1])
    return [item[1] for item in sorted(reduce(append_unique, srt_enum, [srt_enum[0]]))]


def main():
    options = parse_args()

    if options.cookie is not None:
        # Log in with browser and use --cookie=ABCDEF012345 commandline argument
        auth = options.cookie
    elif options.no_auth is True:
        # Don't use authentication when it's not needed
        auth = None
    else:
        # Basic Auth is usually easier for scripts like this to deal with than Cookies.
        user = options.user if options.user is not None \
                    else input('Username: ')
        password = options.password if options.password is not None \
                    else getpass.getpass('Password: ')
        auth = (user, password)

    jira = JiraSearch(options.jira_url, auth, options.no_verify_ssl)

    if options.jql_query is not None:
        options.issues.extend(jira.list_ids(options.jql_query))

    graph = []
    for issue in options.issues:
        graph = graph + build_graph_data(issue, jira, options.excludes, options.show_directions, options.directions,
                                         options.includes, options.issue_excludes, options.closed, options.ignore_epic,
                                         options.ignore_subtasks, options.traverse, options.word_wrap)

    if options.local:
        print_graph(filter_duplicates(graph), options.node_shape)
    else:
        create_graph_image(filter_duplicates(graph), options.image_file, options.node_shape)


if __name__ == '__main__':
    main()
