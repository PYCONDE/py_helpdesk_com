import datetime

import omegaconf
import pytest

from app import helpdesk, CONFIG

conf_mock = omegaconf.OmegaConf.create(
    {
        "api_credentials": {
            "account": "dummy_uuid-id-of-some-sort-2547",
            "entity_id": "noone@test.com",
            "token": "dal:jibberischjibber",
        }
    }
)

