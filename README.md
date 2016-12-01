jira-dependency-graph
=====================

Graph visualizer for dependencies between JIRA tickets. Takes into account subtasks and issue links.

Uses JIRA rest API v2 for fetching information on issues.
Uses [Google Chart API](https://developers.google.com/chart/) for graphical presentation.

Requirements:
=============
* Python 2.6+
* [requests](http://docs.python-requests.org/en/master/)

Usage:
======
```bash
$ git clone https://github.com/pawelrychlik/jira-dependency-graph.git
$ virtualenv .virtualenv && source .virtualenv/bin/activate # OPTIONAL
$ pip install -r requirements.txt
$ cd jira-dependency-graph
$ python jira-dependency-graph.py --user=your-jira-username --password=your-jira-password --jira=url-of-your-jira-site issue-key

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

Google Chart request:
http://chart.apis.google.com/chart?cht=gv&chl=digraph{"JIRATICKET-2451"->"JIRATICKET-3853"[arrowhead=empty][label="is+blocked+by"];"JIRATICKET-2451"->"JIRATICKET-3968"[arrowhead=empty][label="is+blocked+by"];"JIRATICKET-2451"->"JIRATICKET-3126"[arrowhead=empty][label="is+blocked+by"];"JIRATICKET-2451"->"JIRATICKET-2977"[arrowhead=empty][label="is+blocked+by"];"JIRATICKET-3853"->"JIRATICKET-2451"[arrowhead=empty][label="blocks"];"JIRATICKET-3853"->"JIRATICKET-3968"[arrowhead=empty][label="relates+to"];"JIRATICKET-3968"->"JIRATICKET-2451"[arrowhead=empty][label="blocks"];"JIRATICKET-3968"->"JIRATICKET-3853"[arrowhead=empty][label="relates+to"];"JIRATICKET-3126"->"JIRATICKET-2451"[arrowhead=empty][label="blocks"];"JIRATICKET-3126"->"JIRATICKET-3571"[arrowhead=empty][label="testing+discovered"];"JIRATICKET-3571"->"JIRATICKET-3126"[arrowhead=empty][label="discovered+while+testing"]    ;"JIRATICKET-2977"->"JIRATICKET-2451"[arrowhead=empty][label="blocks"]}

Writing to issue_graph.png

```
Result:
![Example result](examples/issue_graph.png)

Local Usage:
============
If you have issues with the Google Graphviz API limitations you can use your local graphviz installation like this:

```bash
$ git clone https://github.com/pawelrychlik/jira-dependency-graph.git
$ cd jira-dependency-graph
$ python jira-dependency-graph.py --user=your-jira-username --password=your-jira-password --jira=url-of-your-jira-site --local issue-key | dot -Tpng > issue_graph.png
```

Advanced Usage:
===============
In case you have specific issue links you don't want to see in your graph, you can exclude them:

```bash
$ python jira-dependency-graph.py --user=your-jira-username --password=your-jira-password --jira=url-of-your-jira-site --exclude-link 'is required by' --exclude-link 'duplicates' issue-key
```

The grapher will still walk the link, just exclude the edge. This especially useful for bidirectional links and you only
want to see one of them, e.g. *depends on* and *is required by*.

Notes:
======
Based on: [draw-chart.py](https://developer.atlassian.com/download/attachments/4227078/draw-chart.py) and [Atlassian JIRA development documentation](https://developer.atlassian.com/display/JIRADEV/JIRA+REST+API+Version+2+Tutorial#JIRARESTAPIVersion2Tutorial-Example#1:GraphingImageLinks), which seemingly was no longer compatible with JIRA REST API Version 2.

There is a limit on the query length: "The longest URL that Google accepts in a chart GET request is 2048 characters in length, after URL-encoding" (from [faq](https://developers.google.com/chart/image/faq)).
