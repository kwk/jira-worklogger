#!/bin/env python3

import logging.config
from jira import JIRA
from jira.client import ResultList
from jira.resources import Issue
from jira.exceptions import JIRAError
import questionary
import sys
import pathlib
import logging
import datetime
import configparser
import dataclasses
from collections.abc import Callable

logging.basicConfig(level=logging.INFO)

@dataclasses.dataclass(kw_only=True)
class Server:
    auth_type: str = "pat"
    url: str
    name: str
    pat: str = ""


class Config:
    def __init__(self):
        self.servers: list[Server] = []
        self.config_dir = pathlib.Path.home().joinpath(
            pathlib.Path(".config/jira-worklogger/")
        )
        self.config_path = self.config_dir.joinpath("jira-worklogger.conf")
        self._parser: configparser.ConfigParser = None

    def load(self):
        # Ensure config file exists and if not create it
        self.config_dir.mkdir(exist_ok=True)
        self.config_path.touch(exist_ok=True)

        self._parser = configparser.ConfigParser()
        self._parser.read(filenames=self.config_path, encoding="utf-8")

        self.servers: list[Server] = []
        for section in self._parser.sections():
            url = self._parser.get(section=section, option="url")
            auth_type = self._parser.get(section=section, option="auth_type")
            if auth_type != "pat":
                raise Exception(
                    f"""The config file {self.config_path} has set the "auth_type" for section "{section}" to "{auth_type}" but only "pat" is supported now."""
                )
            pat = self._parser.get(section=section, option="pat")
            self.servers.append(
                Server(auth_type=auth_type, url=url, name=section, pat=pat)
            )

    def write(self, autoreload: bool = True):
        with open(self.config_path, "w") as f:
            self._parser.write(f)
        if autoreload:
            self.load()

    def add_server(self, s: Server):
        section = s.name
        self._parser.add_section(section=section)
        self._parser.set(section=section, option="url", value=s.url)
        self._parser.set(section=section, option="auth_type", value="pat")
        self._parser.set(section=section, option="pat", value=s.pat)
        self.write()

def validate_server_name(c: Config) -> Callable[[str], str|bool]:
    """Returns a function that can be used to validate a server name.

    Args:
        c (Config): The configuration can be used to check if a server name is already taken.

    Returns:
        Callable[[str], str|bool]: A function to be used in the validate argument of a questionary text.
    """
    def validate(name: str):
        if len(name) <= 0:
            return "Please, enter a name for the server!"
        if c._parser.has_section(name):
            return "Name is already taken, please choose another one!"
        return True

    return validate

def add_new_server_questions(c: Config) -> Server:
    url = questionary.text(
        message="Which JIRA server to connect to?",
        default="https://issues.redhat.com",
        validate=lambda text: (
            True if len(text) > 0 else "Please, enter a JIRA server"
        ),
    ).unsafe_ask()
    name = questionary.text(
        message="What name to give your server?",
        default="Red Hat",
        validate=validate_server_name(c),
    ).unsafe_ask()
    # For a new PAT go to:
    # https://issues.redhat.com/secure/ViewProfile.jspa?selectedTab=com.atlassian.pats.pats-plugin:jira-user-personal-access-tokens
    pat = questionary.password(
        message="What is your JIRA Personal Access Token (PAT)?",
        validate=lambda text: True if len(text) > 0 else "Please enter a value",
    ).unsafe_ask()
    return Server(auth_type="pat", url=url, name=name, pat=pat)


def add_new_server(c: Config):
    """Asks a few questions to add a new server configuration to the config"""
    s = add_new_server_questions(c)
    c.add_server(s)


def main(args=None):
    """The main program"""
    config = Config()
    config.load()

    if len(config.servers) == 0:
        add_new_server(config)

    server: Server = None
    while server is None:
        server_choices = [
            questionary.Choice(title=f"{s.name} - {s.url}", value=s) for s in config.servers
        ]
        server_choices.append(questionary.Separator())
        server_choices.append(
            questionary.Choice(title="Add a new server", value="add_new_server")
        )
        s = questionary.select(
            message="Please select a server to work with", choices=server_choices
        ).unsafe_ask()
        if s == "add_new_server":
            add_new_server(config)
        else:
            server = s

    # Some Authentication Methods
    jira = JIRA(
        server=server.url,
        token_auth=server.pat,
    )

    # Who has authenticated
    myself = jira.myself()
    logging.debug(
        f"You're authenticated with JIRA ({server.url}) as: {myself['name']} - {myself['displayName']} ({myself['emailAddress']})"
    )

    # Which field to pull from the JIRA server for each issue
    pull_issue_fields = ["id", "key", "summary", "statusCategory", "status", "description"]

    # List all open issue by the current user
    issues: ResultList[Issue] = jira.search_issues(
        jql_str="assignee=currentUser() AND statusCategory not in (Done)",
        fields=pull_issue_fields,  # or simply comment out to get all fields
    )

    # Build list of issues to select from
    issue_choices = [
        questionary.Choice(
            title=f"{issue.key} - {issue.fields.summary}",
            description=f"Status: {issue.fields.status}",
            value=f"{issue.key}",
        )
        for issue in issues
    ]
    issue_choices.append(questionary.Separator())
    issue_choices.append(
        questionary.Choice(
            title="My issue is not listed, enter manually", value="manually_enter_issue_key"
        )
    )

    # Repeatedly ask for which issue to select and make sure it is found in case the
    # issue key was entered manually.
    issue_keys = []
    issues_found = False
    while not issues_found:
        try:
            issue_keys = questionary.checkbox(
                message="Which issue(s) do you work on?",
                instruction="You can use the arrow keys to select an issue or start to type to filter the list. If your issue is not in the list, select the bottom option to enter the JIRA key manually.",
                choices=issue_choices,
                use_search_filter=True,
                use_jk_keys=False,  # Has to be disabled when using search filter,
            ).unsafe_ask()
        except KeyboardInterrupt:
            questionary.print("Cancelled by user. Exiting.")
            sys.exit(1)

        # Check if anything was selected
        if issue_keys is None or issue_keys == []:
            continue

        if issue_keys == ["manually_enter_issue_keys"]:
            issue_keys = [
                questionary.text(
                    message="What is the key you work on?",
                    instruction="e.g. JIRA-1234",
                    validate=lambda text: (
                        True if len(text) > 0 else "Please enter a value"
                    ),
                ).unsafe_ask()
            ]

        # Load selected issues to ensure they all exist
        # TODO(kwk): Can we do this in parallel somehow?
        try:
            for issue_key in issue_keys:
                logging.debug(f"Loading issue f{issue_key}")
                jira.issue(id=issue_key, fields=["id", "key"])
        except JIRAError as ex:
            questionary.print(f"Failed to find issue with key '{issue_keys}': {ex.text}")
            questionary.print("Please select issues again.")
        else:
            issues_found = True
            logging.debug("All issues exist")

    log_method = questionary.select(
        message="How do you want to log the time?",
        default="auto",
        choices=[
            questionary.Choice(
                title="Automatically (with a timer)",
                description="We will start a timer so you can start working and later come back.",
                value="auto",
                shortcut_key="a",
            ),
            questionary.Choice(
                title="Manually",
                description='You can enter something like "1h" or "2w".',
                value="manual",
                shortcut_key="m",
            ),
        ],
    ).unsafe_ask()

    time_spent = 0

    if log_method == "manual":
        time_spent = questionary.text(
            message='How much time did you time spent, e.g. "2d", or "30m"?',
            validate=lambda text: True if len(text) > 0 else "Please enter a value",
        ).unsafe_ask()

    if log_method == "auto":
        questionary.press_any_key_to_continue(
            message="Press any key to START the timer..."
        ).unsafe_ask()
        start_time = datetime.datetime.now()
        questionary.press_any_key_to_continue(
            message="You can do your work now and come back when you're done. Then press any key to STOP the time logging..."
        ).unsafe_ask()
        stop_time = datetime.datetime.now()
        seconds_spent = (stop_time - start_time).total_seconds()
        minutes_spent = round(seconds_spent / 60.0, 2)
        time_spent = f"{minutes_spent}m"
        questionary.print(text=f"We've tracked a total of {time_spent} minutes.")

    comment = questionary.text(
        message="Enter an optional comment for what you've worked on:", multiline=True
    ).unsafe_ask()

    # Finally update the worklog of all issues
    for issue_key in issue_keys:
        logging.debug(f"Adding worklog for f{issue_key}.")
        jira.add_worklog(
            issue=issue_key,
            timeSpent=time_spent,
            adjustEstimate="auto",
            comment=comment,
        )
        questionary.print(f"Added worklog to issue {issue_key}")

    questionary.print(text="Thank you for using this tool.")

def cli(args=None):
    try:
        main(args)
    except KeyboardInterrupt:
        questionary.print("Cancelled by user. Exiting.")
        sys.exit(1)
