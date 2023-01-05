from app.helpdesk import PyHelpDesk


class PyHelpDeskFinAid2023(PyHelpDesk):
    """
    Methods used for handling Fin Aid
    """


    def get_tickets_tagged(self, tags):
        """
        Agents can add tags to tickets.
        Retrieve tickets with those tags. Used for FinAid in 2022.
        Processed should not use tags in the future. Kept for reference.
        Args:
            tags:

        Returns:

        """
        tag_ids = self.get_ids_for_tags(tags)
        excluded_tags = ["recipient:rejected"]
        excluded_tag_ids = {self.get_tag_id_for_tag_name(x) for x in excluded_tags}
        params = {"tagIDs": self.get_ids_for_tags(tags)}
        # OR-SEARCH: this will find any ticket with any of the tags
        tickets = self.get_tickets(params)
        tickets = [x for x in tickets if all([y in x.get("tagIDs") for y in tag_ids])]
        granted_tickets = [
            x for x in tickets if not (set(x.get("tagIDs")) & excluded_tag_ids)
        ]
        return granted_tickets

    def get_all_tickets_online_accepted(self):
        """
        Agents can add tags to tickets.
        Retrieve tickets with those tags. Used for FinAid in 2022.
        Processed should not use tags in the future. Kept for reference.

        Returns:

        """
        tags = ["accepted", "online-ticket"]
        return self.get_tickets_tagged(tags)

    def get_all_tickets_in_person_accepted(self):
        tags = ["accepted", "in-person-ticket"]
        return self.get_tickets_tagged(tags)
