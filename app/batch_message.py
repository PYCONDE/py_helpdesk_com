from omegaconf import DictConfig
from pydantic import BaseModel, EmailStr, Extra

from app import CONFIG
from app.helpdesk import PyHelpDesk


class Recipient(BaseModel, extra=Extra.allow):
    """
    How to address and contact a person.
    """

    name: str
    email: str
    address_as: str = ""  # could be the first name

    def __init__(self, **data):
        if not data.get("address_as"):
            data["address_as"] = data["name"]
        super().__init__(**data)


class BatchMessage(BaseModel, extra=Extra.allow):
    """
    Same message to be sent to a list of Recipients
    """

    subject: str
    message_text: str
    team_id: str
    agent_id: str
    status: str = "solved"
    recipients: list[Recipient]

    def __init__(self, **data):
        self.validate_api_inputs(**data)
        super().__init__(**data)

    @classmethod
    def validate_api_inputs(cls, **data):
        """Invalid values will fail calling the helpdesk API: validate team_id, agent_id and ticket status"""
        basic_helpdesk = PyHelpDesk(CONFIG.api_credentials)
        assert data["team_id"] in basic_helpdesk.teams
        assert data["agent_id"] in basic_helpdesk.agents
        assert basic_helpdesk.is_valid_ticket_status(data["status"])


class PyHelpDeskMailing(PyHelpDesk):
    """Create a mass mailings by a given input"""

    def __init__(self, api_credentials: DictConfig, batch_message: BatchMessage):
        super().__init__(api_credentials)
        self.message: BatchMessage = batch_message

    def batch_message(self):
        for recipient in self.message.recipients:
            try:
                message = self.customize_message(recipient)
                res = self.create_new_ticket(
                    recipient.email,
                    recipient.name,
                    self.message.subject,
                    message,
                    self.message.team_id,
                    self.message.agent_id,
                    self.message.status,
                )
                if res.status_code == 200:
                    print("successfully sent message")
                    continue
                print(res.status_code)
                a = 44

            except Exception as e:
                print(e)

    def customize_message(self, recipient):
        """Customize messages for recipients. Inject class params into the message_text

        Add attributes to use in handle bars into the message_text like:
        Assume: recipient = Recipient(name="Peter Parker", email="spidi@web.com", address_as="Spiderman")

        Hello {recipient.address_as},
        We hope it's ok to address you your first name rather than using your full name being {recipient.name}.
        Have you read the email's subject '{self.message.subject}'?
        Cheers!

        """
        customized_message = self.message.message_text.format(recipient=recipient, self=self)
        return customized_message

