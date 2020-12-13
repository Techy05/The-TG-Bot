import os


class ENV(object):
    LOGGER = True
    MAX_MESSAGE_SIZE_LIMIT = 4095  # TG API Limit
    LOAD = []
    NO_LOAD = []
    HELPER = {}
    DB_URI = os.environ.get("DATABASE_URL", None)
    APP_ID = int(os.environ.get("APP_ID", 1))
    API_HASH = str(os.environ.get("API_HASH", "None"))
    SESSION = os.environ.get("SESSION", None)
    LOGGER_GROUP = int(os.environ.get(
        "LOGGER_GROUP", 0))
    DOWNLOAD_DIRECTORY = os.environ.get(
        "DOWNLOAD_DIRECTORY", "./DOWNLOADS/")
    ANTI_PM_SPAM = bool(os.environ.get("ANTI_PM_SPAM", True))
    MAX_PM_FLOOD = int(os.environ.get("MAX_PM_FLOOD", 5))
    COMMAND_HANDLER = os.environ.get("COMMAND_HANDLER", "\.")
    SUDO_USERS = os.environ.get("SUDO_USERS", "").split()
    BLACK_LIST = set(int(x) for x in os.environ.get(
        "BLACK_LIST", "").split())
    DRIVE_CLIENT_ID = os.environ.get("DRIVE_CLIENT_ID", None)
    DRIVE_CLIENT_SECRET = os.environ.get("DRIVE_CLIENT_SECRET", None)
    DRIVE_AUTH_TOKEN_DATA = os.environ.get("DRIVE_AUTH_TOKEN_DATA", None)
    DRIVE_PARENT_ID = os.environ.get("DRIVE_PARENT_ID", None)
    INDEX_URL = os.environ.get("INDEX_URL", None)
    LYDIA_API = os.environ.get("LYDIA_API", None)
    GITHUB_REPO_LINK = os.environ.get(
        "GITHUB_REPO_LINK", "https://github.com/justaprudev/The-TG-Bot").split()[0]
    HEROKU_API_KEY = os.environ.get("HEROKU_API_KEY", None)
    TG_APP_NAME = os.environ.get("TG_APP_NAME", None)
    BOT_TOKEN = os.environ.get("BOT_TOKEN", None)
    BOT_USERNAME = os.environ.get("BOT_USERNAME", None)
    STICKER_PACK = os.environ.get("STICKER_PACK", None)
    UNLOCKED_CHATS = os.environ.get("UNLOCKED_CHATS", [])
    RMBG_API_KEY = os.environ.get("RMBG_API_KEY", None)


class _ENV(ENV):
    pass
    # Add values here to use for development