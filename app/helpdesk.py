import json
import datetime
import requests
from omegaconf import DictConfig
from requests.auth import HTTPBasicAuth

from app import CONFIG

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "pysv api",  # important, always use a custom User-Agent, never a generic one.
    # generic User-Agents are filtered by helpdesk to reduce spam.
}


class APIException(Exception):
    """Errors communicating with helpdesk API"""


class PyHelpDesk:
    """Basic functionalities for Helpdesk interactions."""

    def __init__(self, api_credentials: DictConfig):
        self.authentication = HTTPBasicAuth(api_credentials.account, api_credentials.token)
        self.all_tags = []
        self._teams = {}  # dict with teams by name and ID
        self._agents = {}  # dict with agent by name and ID

    def get_from_api(self, url, params=None):
        """Wrapper for GET calls to API

        Raises:
            APIException if status code is not 200
        """
        if not params:
            params = {}

        res = requests.get(url, auth=self.authentication, params=params, headers=headers)
        if res.status_code == 200:
            return res.json()
        raise APIException(
            f"{res.status_code}: {res.reason}: {json.loads(res.content)['error']}, {json.loads(res.content)['details']}"
        )

    def get_tickets(self, params) -> dict:
        """Get all tickets for a filter.

        Used for:
        - archiving
        Could also be used for:
        - Handling specific responses (ie search for keywords of IDs in text)

        Args:
            params: filter to apply

        Returns:
            Full response from helpdesk.com API as dict
        """
        params["pageSize"] = 100
        url = "https://api.helpdesk.com/v1/tickets"
        return self.get_from_api(url, params)

    def get_ids_for_tags(self, tags):
        return [self.get_tag_id_for_tag_name(x) for x in tags]

    def get_tag_id_for_tag_name(self, name):
        filtered = [x for x in self.tags if x.get("name", "") == name]
        if filtered:
            return filtered[0].get("ID")

    def create_new_ticket(
        self,
        requester_email,
        requester_name,
        subject,
        message_text: str,
        team_id: str,
        agent_id: str,
        status="solved",
    ):
        """Add a new ticket to the helpdesk.

        Adding a new ticket will also email the recipient.
        Replies to that email will all go to a helpdesk thread keeping the communication
        together and accessible to the team.

        Args:
            requester_email:
            requester_name:
            subject:
            message_text:
            team_id:
            agent_id:
            status:

        Returns:

        """
        data = {
            "status": status,
            "subject": subject,
            "message": {"text": message_text},
            "requester": {"email": requester_email, "name": requester_name},
            "teamIDs": [team_id],
            "assignment": {
                "team": {
                    "ID": team_id,
                },
                "agent": {"ID": agent_id},
            },
        }
        res = requests.post(
            "https://api.helpdesk.com/v1/tickets",
            auth=self.authentication,
            data=json.dumps(data),
            headers=headers,
        )
        return res

    def tickets_by_date_range(self, from_date: datetime.datetime = None, to_date: datetime.datetime = None):
        params = {}
        if from_date:
            params["createdDateFrom"] = self.api_iso_timestamp(from_date)
        if to_date:
            params["createdDateTo"] = self.api_iso_timestamp(to_date)
        return self.get_tickets(params)

    @classmethod
    def api_iso_timestamp(cls, some_datetime):
        """Timestamp format as expected by API"""
        return f'{some_datetime.isoformat(timespec="seconds")}Z'

    @property
    def teams(self) -> dict:
        if not self._teams:
            self.update_teams()
        return self._teams

    def helpdesk_teams(self):
        res = requests.get(
            "https://api.helpdesk.com/v1/teams",
            auth=self.authentication,
            headers=headers,
        )
        return res

    def update_teams(self):
        """
        Dictionary of all teams: ID and team name.

        Useful to filter tickets where a team ID is required.

        Returns:
            dict with all team_id: name and name: team_id

        """
        res = self.helpdesk_teams()
        if res.status_code != 200:
            raise ValueError("Request for teams failed, aborting.")
        res = res.json()
        team_file = CONFIG.docs_cache_path / "teams.json"
        teams = {k["name"]: k["ID"] for k in res}
        teams.update({v: k for k, v in teams.items()})
        with team_file.open("w") as f:
            json.dump(teams, f, indent=4)
        self._teams = teams

    @property
    def agents(self) -> dict:
        if not self._agents:
            self.update_agents()
        return self._agents

    def helpdesk_agents(self):
        return self.get_from_api("https://api.helpdesk.com/v1/agents")

    def update_agents(self):
        """Dictionary of all agents: ID and agent name.

        Returns:
            dict with all agent_id: name and name: agent_id

        """

        def filter_agents(_list):
            roles = [
                "normal",
                "owner",
            ]  # active agents only - filter inactive / watchers
            return {k["name"]: k["ID"] for k in _list if any([r in k["roles"] for r in roles])}

        self._agents = self._update("agents", self.helpdesk_agents, filter_agents)

    @classmethod
    def _update(cls, topic: str, update_func: callable, filter_func) -> dict:
        """Generic function: Retrieve data from API and return this data mangled by the filter function

        Args:
            topic: descriptive name like teams, agents,... Is used as filename.
            update_func: returns the data from the API
            filter_func: handles the data mangling, should always return a simple dict k:v

        Returns:
            dict
        """
        try:
            res = update_func()
        except APIException:
            raise ValueError(f"Request for {topic} failed, aborting.")
        _file = CONFIG.docs_cache_path / f"{topic}.json"
        _dict = filter_func(res)
        _dict.update({v: k for k, v in _dict.items()})
        with _file.open("w") as f:
            json.dump(_dict, f, indent=4)
        return _dict

    @property
    def tags(self):
        if not self.all_tags:
            self.update_tags()
        return self.all_tags

    def update_tags(self):
        url = "https://api.helpdesk.com/v1/tags"
        all_tags = self.get_from_api(url)
        self.all_tags = all_tags.json()

    @property
    def ticket_statuses(self) -> tuple:
        return "open", "pending", "onhold", "solved"

    def is_valid_ticket_status(self, ticket_status) -> bool:
        return ticket_status in self.ticket_statuses

    def init(self):
        self.update_agents()
        self.update_teams()
