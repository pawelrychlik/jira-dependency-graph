FROM python:3.6

ADD jira-dependency-graph.py /jira/
ADD requirements.txt /jira/
ADD personal-config.ini /jira/
WORKDIR /jira
RUN apt-get update \
  && apt-get install -y --no-install-recommends graphviz \
  && rm -rf /var/lib/apt/lists/* \
  && pip install -r requirements.txt
