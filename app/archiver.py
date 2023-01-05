import datetime
import json
from uuid import uuid4

import requests

from app import CONFIG
from app.helpdesk import PyHelpDesk


class PyHelpDeskCleaner(PyHelpDesk):
    """
    Methods for archiving and cleanup once a conference is closed.
    DANGER ZONE! Can delete tickets, handle with care!
    """

    def archive_old_tickets(self, include_teams: list[str], to_date: datetime, *, yield_results=False):
        """Archive tickets from previous conferences.

        Args:
            include_teams: at least one team must be provided
              teams is an uuid
            to_date: archive tickets until this timestamp
            yield_results: use function as generator

        Returns:
            json

        """
        threshold: int = 90  # days
        if to_date + datetime.timedelta(days=threshold) > datetime.datetime.now():
            raise ValueError(f"Never delete tickets younger than {threshold} days")
        params = {"createdDateTo": self.api_iso_timestamp(to_date)}
        for i, team_id in enumerate(include_teams):
            params["teamIDs[]"] = team_id  # team the ticket is visible to, teamIDs params requires [] notation
            team_tickets = self.get_tickets(params)
            if not team_tickets:
                print(f"{self.teams[team_id]} has nothing left to be archived")
                continue
            archive_name = f"a_{self.teams[team_id]}_{self.api_iso_timestamp(to_date)}_{i:02d}_{uuid4().hex[:4]}.json"
            archive_name = archive_name.replace("/", "-").replace(":", "-")  # remove chars use in paths
            with (CONFIG["archive_path"] / archive_name).open("w") as f:
                print(f"{self.teams[team_id]} archiving {len(team_tickets)}")
                json.dump(team_tickets, f)
            if yield_results:
                yield team_tickets

    def archive_and_delete_tickets(self, include_teams: list[str], to_date: datetime):
        """Wrapper to archive and delete in on step."""
        for tickets_archived in self.archive_old_tickets(include_teams, to_date, yield_results=True):
            tickets_ids_to_delete = [x["ID"] for x in tickets_archived]
            print(f"deleting {len(tickets_ids_to_delete)}")
            self.delete_tickets(tickets_ids_to_delete)
        yield

    def delete_tickets(self, ticket_ids: list[str]):
        print(f"{len(ticket_ids)} ticket_id to delete")
        for ticket_id in ticket_ids:
            try:
                res = self.delete_ticket(ticket_id)
                if res.status_code == 200:
                    print("deleted", ticket_id)
                else:
                    print("error", res.status_code, ticket_id)
            except Exception as e:
                print(f"{ticket_id}: {e}")

    def delete_ticket(self, ticket_id: str):
        res = requests.delete(f"https://api.helpdesk.com/v1/tickets/{ticket_id}", auth=self.authentication)
        return res

    def standard_maintenance(self, year):
        """Remove all tickets filed until 30. September of previous year.
        MAKE SURE archive_teams is up-to-date, updated helpdesks if needed.
        """
        archive_teams = [
            # 'General Helpdesk'
            "031061f2-195e-4f1f-8e08-67db15beabda",
            # 'Program/Speakers'
            "3f68251e-17e9-436f-90c3-c03b06a72472",
            # 'Diversity Committee'
            "89ac36d6-2e58-43ee-a519-a098ed7a6f82",
            # 'Sponsoring' - always keep
            # 'c083236a-bb25-413f-86a1-e6b14452175a',
            # 'PySV' - always keep
            # '3825302c-0599-4bae-bbf2-e8be2f37573f',
        ]
        archive_until_date = datetime.datetime(year, 9, 30)
        self.archive_and_delete_tickets(archive_teams, archive_until_date)
