jira-dependency-graph
=====================

Graph visualizer for dependencies between JIRA tickets.

Uses JIRA rest API v2 for fetching information on issues.
Uses [Google Chart API](https://developers.google.com/chart/) for graphical presentation.

Requirements:
=============
* Python 2.6+
* [restkit](https://github.com/benoitc/restkit)

Usage:
======
    $ git clone https://github.com/pawelrychlik/jira-dependency-graph.git
    $ cd jira-dependency-graph
    $ python jira-dependency-graph.py --user=your-jira-username --password=your-jira-password --jira=url-of-your-jira-site issue-key

    # e.g.:
    $ python jira-dependency-graph.py --user=pawelrychlik --password=s3cr3t --jira=https://your-company.jira.com JIRATICKET-718
    
    Fetching JIRATICKET-718
    Fetching JIRATICKET-5461
    Fetching JIRATICKET-5462
    Fetching JIRATICKET-5463
    Fetching JIRATICKET-719
    Fetching JIRATICKET-5356
    Writing to issue_graph.png

Notes:
======
Based on: [draw-chart.py](https://developer.atlassian.com/download/attachments/4227078/draw-chart.py) and [Atlassian JIRA development documentation](https://developer.atlassian.com/display/JIRADEV/JIRA+REST+API+Version+2+Tutorial#JIRARESTAPIVersion2Tutorial-Example#1:GraphingImageLinks), which seemingly was no longer compatible with JIRA REST API Version 2.

There is a limit on the query lenght: "The longest URL that Google accepts in a chart GET request is 2048 characters in length, after URL-encoding" (from [faq](https://developers.google.com/chart/image/faq)).