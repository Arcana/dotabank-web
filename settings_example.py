import os

APP_DIR = os.path.abspath(os.path.dirname(__file__))
UGC_FILES_DIR = os.path.join(APP_DIR, 'ugcfiles')

STEAM_API_KEY = ""  # TODO
STEAM_API_TIMEOUT = 10
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
    'CACHE_TYPE': "app.cache.dotabank_filesystem",
    'CACHE_DIR': APP_DIR + os.sep + '.cache',
    #'CACHE_DEFAULT_TIMEOUT',
    #'CACHE_ARGS',
    #'CACHE_OPTIONS'
}

ENCRYPTION_KEY = ""  # 16, 24, or 32 bytes long  # TODO

# Amazon info
AWS_REGION = ""  # TODO
AWS_ACCESS_KEY_ID = ""  # "dotabank"  # TODO
AWS_SECRET_ACCESS_KEY = ""  # TODO
AWS_BUCKET = ""  # TODO
AWS_SQS_GC = ""  # TODO
AWS_SQS_DL = ""  # TODO

# Recaptcha info

RECAPTCHA_PUBLIC_KEY = ""  # TODO
RECAPTCHA_PRIVATE_KEY = ""  # TODO

# Sentry (getsentry.com) info
SENTRY_DSN = ""

# General vars
CONTACT_EMAIL = ""  # TODO
REPLAY_DOWNLOAD_TIMEOUT = 60 * 15  # Seconds; 15 minutes.
REPLAYS_PER_PAGE = 32
USERS_PER_PAGE = 32
LATEST_REPLAYS_LIMIT = 8
USER_OVERVIEW_LIMIT = 10
LOGS_PER_PAGE = 32
BITCOIN_DONATION_ADDRESS = ""  # TODO
DATE_STRING_FORMAT = "%d %b %Y, %H:%M"
SHORT_DESCRIPTION_LENGTH = 140

GC_MATCH_REQUSTS_RATE_LIMIT = 100
GC_PROFILE_REQUSTS_RATE_LIMIT = 250

MASS_DOWNLOAD_MAX_COUNT = 10

CAPTCHA_LEAGUE_EXCEPTIONS = []  # Captcha-less downloading of TI4

MAX_REPLAY_FIX_ATTEMPTS = 5

# Stripe payments
STRIPE_DEBUG_SECRET_KEY = ""
STRIPE_DEBUG_PUBLISHABLE_KEY = ""
STRIPE_PROD_SECRET_KEY = ""
STRIPE_PROD_PUBLISHABLE_KEY = ""


# Dater update timeouts
UPDATE_LEAGUES_TIMEOUT = 60 * 60 * 6  # Minutes; 6 hours
UPDATE_LEAGUES_IN_DEBUG = False  # Don't update leagues table when running in debug mode.
