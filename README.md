# Interface to Helpdesk

For the conference we use helpdesk.com to communicate with attendees, speakers and sponsors as tea via a helpdesk.

This repo is a wrapper around the helpdesk.com REST API to simply interactions in regard
to conference related communication.

## Set-Up

```
git clone

cd py_helpdesk_com
```

Required packages are listed in `environment.yml`.

```
conda con create --file environment.yml

conda activate py_helpdesk_com
```

### API Access

To access the helpdesk.com API you require a Helpdesk Auth Token.

````yaml
api_credentials:
  "account": "some uuid"
  "entity_id": "helpdesk_email@team"
  "token": "ticKtacktokEN"
````

Store your credentials in `_private/config.yaml`

**Use the same (shared) email you use to log into helpdesk to create the token".**
See here how to create:  https://www.youtube.com/watch?v=-EUZ_Ynvz5Q&t=32s
In case there are problems with livechat subscription trails, contact an helpdesk admin.

## Init
You need some additional ids to interact with helpdesk, as team and agent IDs.

Run this once you have your API credentials.

```bash
# make sure to set the PYTHONPATH, apps like PyCharm will handle this for you.
export PYTHONPATH=`pwd`

python app/init.py
```

Check `./docs_cache` for:
- [teams.json](docs_cache/teams.json)
- [agents.json](docs_cache/agents.json)


## Structure

### PyHelpDesk

Is a base class with common functionalities

### PyHelpDeskMailing

Create a batch mailing including customization.

We utilize pydantic models to validate the date beforehand:

#### `Recipient`

The person to receive the message.

Required:

- name: (full) name
- email


Optional:

- address_as: used to address the person "Hi {address_as}," If not provided, fallback to `name`.

#### `BatchMessage`

Required:

- subject
- message_text, see belo for details
- team_id, see [teams.json](docs_cache/teams.json)
- agent_id, see [agents.json](docs_cache/agents.json)
- status, "solved" by default. Can be any of "open", "pending", "onhold", "solved"

##### Message

The message should be a DocString, i.e. three quotes ("""...""").

The message can be a text, e.g.
````python
"""
Hi all,
A quick message without any customization.
Cheers!
"""
````
The text can also contain attributes accessible from withing the `batch_message` method, e.g.
- recipient.address_as
- recipient.name
- any attributes in self, e.g. self.message.subject

```python
"""
Hello {recipient.address_as},
This is an automated test message via our helpdesk!
Looks like we are getting somewhere?
Hope it's ok to call you {recipient.address_as} and not by your full {recipient.name}.
Have you read the email's subject '{self.message.subject}'?
Cheers!
"""
```

```python
test_recipients = [
    Recipient(name="Peter Parker", email="spidi@web", address_as="Spiderman"),
    Recipient(name="Bruce Wayne", email="bruce@wayneindustries.com", address_as="Bruce"),
    Recipient(name="Batman", email="bat@man.com", address_as="Bruce"),
    Recipient(name="Joker", email="mad@house.com"),
]
test_message = BatchMessage(
    subject="API TEST: This is a message",
    message_text="""Hello {recipient.address_as},
        This is an automated test message via our helpdesk!
        Looks like we are getting somewhere?
        Hope it's ok to call you {recipient.address_as} and not by your full {recipient.name}.
        Have you read the email's subject '{self.message.subject}'?
        Cheers!
        """,
    team_id="void---25417e9-436f-90c3-c03b06a72472",  # see docs_cache/teams.json
    agent_id="void---25417e9-436f-90c3-c03b06a72472",  # see docs_cache/agents.json
    status="solved",
    recipients=test_recipients,

)
mailing = PyHelpDeskMailing(CONFIG.api_credentials, test_message)
mailing.batch_message()

```

##### Adding More Attributes in Message

Both `BatchMessage` and `Recipient` models support adding extra attributes. 

If you want to add some extra custom text to the message you can simply:

```python
# add girlfriend
recipients = [Recipient(name="Peter Parker", email="spidi@web", address_as="Spiderman", girlfriend="Mary Jane")]
# message with custom attribute in recipient
custom_message = BatchMessage(
    message_text="""Hello {recipient.address_as},
        Send our regards to your girlfriend {recipient.girlfriend}
        Cheers!
        """,
    recipients=recipients,
    ...
)
mailing = PyHelpDeskMailing(CONFIG.api_credentials, test_message)
mailing.batch_message()
```

### PyHelpDeskFinAid2023

Do not use, in review / refactoring

### PyHelpDeskCleaner

Archive, cleanup after a conference, for admins use only.

## Helpdesk API Docs for Reference

[Helpdesk API](https://api.helpdesk.com/docs#tag/Tickets)

Create Helpdesk Auth Token
https://www.youtube.com/watch?v=-EUZ_Ynvz5Q&t=32s

