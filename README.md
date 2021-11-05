jira-dependency-graph
=====================

Graph visualizer for dependencies between JIRA tickets. Takes into account subtasks and issue links.

Uses JIRA rest API v2 for fetching information on issues.
Uses [Google Chart API](https://developers.google.com/chart/) for graphical presentation.

Example output
==============

![Example graph](examples/issue_graph_complex.png)

Requirements:
=============
* Python 2.7+ or Python 3+
* [requests](http://docs.python-requests.org/en/master/)

Or
* [docker](https://docs.docker.com/install/)

Usage:
======
```bash
$ git clone https://github.com/pawelrychlik/jira-dependency-graph.git
$ virtualenv .virtualenv && source .virtualenv/bin/activate # OPTIONAL
$ cd jira-dependency-graph
$ pip install -r requirements.txt
$ python jira-dependency-graph.py --user=your-jira-username --password=your-jira-password --jira=url-of-your-jira-site issue-key
```

Or if you prefer running in docker:
```bash
$ git clone https://github.com/pawelrychlik/jira-dependency-graph.git
$ cd jira-dependency-graph
$ docker build -t jira .
$ docker run -v $PWD/out:/out jira python jira-dependency-graph.py --user=your-jira-username --password=your-jira-password --jira=url-of-your-jira-site --file=/out/output.png issue-key
```

```
# e.g.:
$ python jira-dependency-graph.py --user=pawelrychlik --password=s3cr3t --jira=https://your-company.jira.com JIRATICKET-718

Fetching JIRATICKET-2451
JIRATICKET-2451 <= is blocked by <= JIRATICKET-3853
JIRATICKET-2451 <= is blocked by <= JIRATICKET-3968
JIRATICKET-2451 <= is blocked by <= JIRATICKET-3126
JIRATICKET-2451 <= is blocked by <= JIRATICKET-2977
Fetching JIRATICKET-3853
JIRATICKET-3853 => blocks => JIRATICKET-2451
JIRATICKET-3853 <= relates to <= JIRATICKET-3968
Fetching JIRATICKET-3968
JIRATICKET-3968 => blocks => JIRATICKET-2451
JIRATICKET-3968 => relates to => JIRATICKET-3853
Fetching JIRATICKET-3126
JIRATICKET-3126 => blocks => JIRATICKET-2451
JIRATICKET-3126 => testing discovered => JIRATICKET-3571
Fetching JIRATICKET-3571
JIRATICKET-3571 <= discovered while testing <= JIRATICKET-3126
Fetching JIRATICKET-2977
JIRATICKET-2977 => blocks => JIRATICKET-2451

Writing to issue_graph.png
```
Result:
![Example result](examples/issue_graph.png)


Advanced Usage:
===============

List of all configuration options with descriptions:

```
python jira-dependency-graph.py --help
```

### Excluding Links

In case you have specific issue links you don't want to see in your graph, you can exclude them:

```bash
$ python jira-dependency-graph.py --user=your-jira-username --password=your-jira-password --jira=url-of-your-jira-site --exclude-link 'is required by' --exclude-link 'duplicates' issue-key
```

The grapher will still walk the link, just exclude the edge. This especially useful for bidirectional links and you only
want to see one of them, e.g. *depends on* and *is required by*.

### Excluding Epics

In case you want to exclude walking into issues of an Epic, you can ignore them:

```bash
$ python jira-dependency-graph.py --user=your-jira-username --password=your-jira-password --jira=url-of-your-jira-site --ignore-epic issue-key
```

### Including Issues

In order to only specify issues with a certain prefix pass in `--issue-include <XXX>` and all tickets will be checked that they match the prefix `XXX`.

### Excluding Issues

By passing in `--issue-exclude`, or `-xi` the system will explicitly ignore the ticket. It can be repeated multiple times, e.g. `-xi MYPR-456 -x MYPR-999` to ignore both issues. 
Use it as a last-resort only, when other means of exclusion do not suit your case, e.g. to omit a part of the graph for better readability.

### Authentication

It is possible to either use the username/password combination or to login via the browser passing in `--cookie <JSESSIONID>`. This logins via the browser and is useful in scenarios where Kerberos authentication is required.

If you are using Atlassian Cloud, use your API token instead of your account password. You can generate one with the following steps:

1. Access https://id.atlassian.com/manage-profile/security/api-tokens.
2. Click "Create API token".
3. Copy the token and store it in a safe place.

More details about API authentication is available in the [official documentation](https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/).

### Closed Issues

By passing in `--ignore-closed` the system will ignore any ticket that is closed.

### Multiple Issues

Multiple issue-keys can be passed in via space separated format e.g.
```bash
$ python jira-dependency-graph.py --cookie <JSESSIONID> issue-key1 issue-key2
```

### JQL Query

Instead of passing issue-keys, a Jira Query Language command can be passed with `--jql` e.g.
```bash
$ python jira-dependency-graph.py --cookie <JSESSIONID> --jql 'project = JRADEV'
```


Usage without Google Graphviz API:
============
If you have issues with the Google Graphviz API limitations you can use your local graphviz installation like this:

```bash
$ git clone https://github.com/pawelrychlik/jira-dependency-graph.git
$ cd jira-dependency-graph
$ python jira-dependency-graph.py --user=your-jira-username --password=your-jira-password --jira=url-of-your-jira-site --local issue-key | dot -Tpng > issue_graph.png
```

*Note*: Its possible that the graph produced is too wide if you have a number of issues. In this case, it is better to firstly pipe the graph to a 'dot' text file e.g.

```bash
$ python jira-dependency-graph.py --jira=url-of-your-jira-site --local issue-key > graph.dot
```

and then process it using `unflatten`:

```bash
unflatten -f -l 4 -c 16 graph.dot  | dot | gvpack -array_t6 | neato -s -n2 -Tpng -o graph.png
```

For a slightly cleaner layout (that preserves the ranks), or if your system doesn't have `unflatten`, you can use `sed` to insert `rankdir=LR;` into the dot file before processing it:
```bash
sed -i 's/digraph{/digraph{ rankdir=LR;/g' graph.dot | dot -o graph.png -Tpng
```

Notes:
======
Based on: [draw-chart.py](https://developer.atlassian.com/download/attachments/4227078/draw-chart.py) and [Atlassian JIRA development documentation](https://developer.atlassian.com/display/JIRADEV/JIRA+REST+API+Version+2+Tutorial#JIRARESTAPIVersion2Tutorial-Example#1:GraphingImageLinks), which seemingly was no longer compatible with JIRA REST API Version 2.

Apologies and Messy Changes:
======
This single commit for the sake of sharing immediately, is less than awesome.  I'd love to come back and clean both the code and the comments, especially since there are other tweaks to come.

Things included in this messy single commit:

1. Getting started, you'll need to create then update `personal-config.ini` with your Jira credentials.  **BEWARE**: do not commit this file, so you don't accidentally share your creds!
```bash
echo "[EXAMPLE]\nJIRA_HOST = https://example.atlassian.net\nJIRA_USER = alice@example.com\nJIRA_PASS = # Create an API key at https://id.atlassian.com/manage-profile/security/api-tokens\n" > personal-config.ini
```

2. For access to multiple organizations, add those additional creds in `personal-config.ini` then specify on the command line with the `--org` option.  The script will default to the first org it finds, unless `--org` is specified.
```bash
--org=EXAMPLE
```

2. Once you've added your creds, if you are aimed at using the docker version, you'll need to build the docker image.  **BEWARE**: This image will contain a copy of your `personal-config.ini` (which contains your Jira creds), so don't share this image unless you intend to share your credentials!
```bash
> docker build -t jira .
```

5. If you prefer to use your own installation of graphviz, you can pipe the output of using `--local` to it, such as
```bash
> docker run -v $PWD/out:/out jira python jira-dependency-graph.py --show-directions=outward --local --word-wrap VOICE-123 | dot -Tpng > ~/Desktop/VOICE-123-graph.png
```

6. The non-`--local` version seemed broken since google isn't handling that endpoint anymore, so Graphviz is now included in the docker image.  i.e., no longer required to use --local then pipe to dot (graphviz) on your host machine.
```bash
> docker run -v $PWD/out:/out jira python jira-dependency-graph.py --show-directions=outward --word-wrap VOICE-123
```

7. An additional artifact when this script is executed without `--local`, will be a PDF version of the diagram, where each node on the diagram hyperlinks you to its corresponding card on jira


8. A new command line option, to automatically update a card with your diagram.  destination card can be any card, whether or not it's related to the diagram:
```bash
--issue-update=<jira-card-key>
```

Wishlist/Upcoming changes:
======
* Improve authentication mechanism, so tokens aren't stored in the clear
* Allow choice of color scheme
* Allow colors to reflect status in the workflow beyond "in progress" and "done" and "else"