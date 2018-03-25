FROM python:2.7-stretch

ADD jira-dependency-graph.py /jira/
ADD requirements.txt /jira/
WORKDIR /jira
RUN pip install -r requirements.txt
