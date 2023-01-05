from app import CONFIG
from app.helpdesk import PyHelpDesk

if __name__ == "__main__":
    help_desk = PyHelpDesk(CONFIG.api_credentials)
    help_desk.init()
