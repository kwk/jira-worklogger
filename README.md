README
======

This command line tool let's you log the time that you've spent on one or more
JIRA issues without the need to click through the JIRA web interface. We allow
you to log the time either automatically (with a timer) or manually (by entering
how much time you've spent in words, e.g. `1h`, `30m`).

Installation
------------

Install `jira-worklogger` from pip using this command:

```console
$ python -m pip install jira-worklogger
```

Demo
----

First time setup and automatic time logging
-------------------------------------------

This demonstration shows how `jira-worklogger` is set up for the first time and
then used to track the time you spent on a JIRA issue automatically. For this,
select at least one issue from your open issues list start the timer. Leave the
terminal open and start working on your issue. When you're done with your work,
come back and press any key to stop the time and log the time in JIRA togethe
with an optional comment.

![](docs/screencapture/automatic-time-logging.gif)

Manual time logging
-------------------

The following demo shows how you can show your issues from a pre-configure JIRA
Server and select one to track the time manually. This is done by giving a
duration like `1h` for one hour or `20m` for twenty minutes.

![](docs/screencapture/manual-time-logging.gif)

Advanced usage and "did"
------------------------

The following demo shows how to work on multiple issues with different tracking methods
as well as how to show your work log using the [did](https://github.com/psss/did) tool.
NOTE: At the time of writing this [my pr](https://github.com/psss/did/pull/429) was not
yet merged into did.

![](docs/screencapture/jira-worklogger-and-did.gif)


Result in JIRA
--------------

In JIRA the result from the two time logs will look like this:

![](docs/screencapture/jira-result.png)

Usage
-----

### Personal access token (PAT)

In order to acquire a personal access token for use with `jira-worklogger` you
have to go to
`https://<YOUR_JIRA_SERVER>/secure/ViewProfile.jspa?selectedTab=com.atlassian.pats.pats-plugin:jira-user-personal-access-tokens`.

For the Red Hat issues, that is [here](https://issues.redhat.com/secure/ViewProfile.jspa?selectedTab=com.atlassian.pats.pats-plugin:jira-user-personal-access-tokens).

### Run from source

Clone the code.

```console
$ git clone https://github.com/kwk/jira-worklogger
$ cd jira-worklogger
```

Install dependencies and set up virtual environment.

```console
$ poetry install
Installing dependencies from lock file

No dependencies to install or update

Installing the current project: jira-worklogger (0.1.0)
```

Run the `jira-worklogger` CLI tool using poetry.

```console
$ poetry run jira-worklogger
? Please select a server to work with (Use arrow keys)
 » Red Hat - https://issues.redhat.com
   ---------------
   Add a new server
```

Build Documentation
===================

To build the documentation, you need the
[`agg`](https://github.com/asciinema/agg) executable in your path.
[`asciinema`](https://github.com/asciinema/asciinema) is needed if you want to
record your own screencaptures.
