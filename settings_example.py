import os

APP_DIR = os.path.abspath(os.path.dirname(__file__))

STEAM_API_KEY = ""  # TODO
DEBUG = False
TESTING = False
SECRET_KEY = ""  # TODO
SQLALCHEMY_DATABASE_URI = ''  # TODO
DEBUG_TB_INTERCEPT_REDIRECTS = False

CACHE_MEMCACHED = {
    'CACHE_TYPE': "memcached",
    'CACHE_MEMCACHED_SERVERS': ["127.0.0.1:11211"],
    'CACHE_KEY_PREFIX': "dotabank",
    #'CACHE_DEFAULT_TIMEOUT',
    #'CACHE_ARGS',
    #'CACHE_OPTIONS'
}

CACHE_FS = {
    'CACHE_TYPE': "filesystem",
    'CACHE_DIR': APP_DIR + os.sep + '.cache',
    #'CACHE_DEFAULT_TIMEOUT',
    #'CACHE_ARGS',
    #'CACHE_OPTIONS'
}

ENCRYPTION_KEY = ""  # 16, 24, or 32 bytes long  # TODO
AWS_REGION = ""  # TODO
AWS_ACCESS_KEY_ID = ""  # "dotabank"  # TODO
AWS_SECRET_ACCESS_KEY = ""  # TODO

AWS_BUCKET = ""  # TODO
AWS_SQS_GC = ""  # TODO
AWS_SQS_DL = ""  # TODO
REPLAY_DOWNLOAD_TIMEOUT = 60 * 15  # Seconds; 15 minutes.

RECAPTCHA_PUBLIC_KEY = "-m0"  # TODO
RECAPTCHA_PRIVATE_KEY = ""  # TODO

# mail server settings
# Mail only allowed to & from tehcnical@dotabank.com
MAIL_SERVER = ''  # TODO
MAIL_PORT = 25  # TODO
MAIL_USERNAME = ""  # TODO
MAIL_PASSWORD = ""  # TODO
MAIL_FROM = ""  # TODO

# administrator list (for E500 email alerts)
ADMINS = []  # TODO


# General vars
CONTACT_EMAIL = ""  # TODO
REPLAYS_PER_PAGE = 32
USERS_PER_PAGE = 32
LATEST_REPLAYS_LIMIT = 8
USER_OVERVIEW_LIMIT = 10
LOGS_PER_PAGE = 32
BITCOIN_DONATION_ADDRESS = ""  # TODO
DATE_STRING_FORMAT = "%d %b %Y, %H:%M"

GC_MATCH_REQUSTS_RATE_LIMIT = 100
GC_PROFILE_REQUSTS_RATE_LIMIT = 250

CAPTCHA_LEAGUE_EXCEPTIONS = [600]  # Captcha-less downloading of TI4
