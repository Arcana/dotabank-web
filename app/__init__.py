from flask import Flask
from flask.ext.cache import Cache
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from flask.ext.sqlalchemy import SQLAlchemy
from raven.contrib.flask import Sentry
import steam
from boto import sqs
from boto.s3.connection import S3Connection

# Create app
app = Flask(__name__)
app.config.from_object("settings")

# Load extensions
mem_cache = Cache(app, config=app.config["CACHE_MEMCACHED"])
fs_cache = Cache(app, config=app.config["CACHE_FS"])
db = SQLAlchemy(app)
login_manager = LoginManager(app)
oid = OpenID(app)

sentry = Sentry(app)

# Setup steamodd
steam.api.key.set(app.config['STEAM_API_KEY'])
steam.api.socket_timeout.set(5)

# Setup AWS SQS
sqs_connection = sqs.connect_to_region(
    app.config["AWS_REGION"],
    aws_access_key_id=app.config["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=app.config["AWS_SECRET_ACCESS_KEY"]
)
sqs_gc_queue = sqs_connection.create_queue(app.config["AWS_SQS_GC"])
sqs_dl_queue = sqs_connection.create_queue(app.config["AWS_SQS_DL"])

# Setup AWS S3
s3_connection = S3Connection(
    aws_access_key_id=app.config["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=app.config["AWS_SECRET_ACCESS_KEY"]
)
dotabank_bucket = s3_connection.get_bucket(app.config["AWS_BUCKET"])

# Setup debugtoolbar if we're in debug mode.
if app.debug:
    from flask.ext.debugtoolbar import DebugToolbarExtension
    toolbar = DebugToolbarExtension(app)


# Set up jinja2 filters.
from filters import escape_every_character,\
    timestamp_to_datestring,\
    datetime_to_datestring,\
    seconds_to_time,\
    dota_wiki_link,\
    dotabuff_hero_link,\
    dotabuff_item_link,\
    dotabuff_match_link
app.add_template_filter(escape_every_character)
app.add_template_filter(timestamp_to_datestring)
app.add_template_filter(datetime_to_datestring)
app.add_template_filter(seconds_to_time)
app.add_template_filter(dota_wiki_link)
app.add_template_filter(dotabuff_hero_link)
app.add_template_filter(dotabuff_item_link)
app.add_template_filter(dotabuff_match_link)


# Load current app version into globals
from .helpers import current_version
app.config['VERSION'] = current_version()


# Load views
import views

# Load blueprints
from app.admin.views import mod as admin_module
from app.users.views import mod as users_module
from app.replays.views import mod as replays_module
from app.leagues.views import mod as leagues_module
from app.teams.views import mod as teams_module
app.register_blueprint(admin_module)
app.register_blueprint(users_module)
app.register_blueprint(replays_module)
app.register_blueprint(leagues_module)
app.register_blueprint(teams_module)

# Set up flask-admin views
from app.admin.views import admin, AdminModelView
from app.users.views import UserAdmin
from app.users.models import Subscription
from app.replays.views import ReplayAdmin, Search, ReplayFavourite, ReplayDownload, ReplayRating
from app.gc.views import GCWorkerAdmin
admin.add_view(UserAdmin(db.session, category="Models"))
admin.add_view(AdminModelView(Subscription, db.session, category="Models"))
admin.add_view(ReplayAdmin(db.session, category="Models"))
admin.add_view(GCWorkerAdmin(db.session, category="Models"))
admin.add_view(AdminModelView(Search, db.session, category="User actions"))
admin.add_view(AdminModelView(ReplayFavourite, db.session, category="User actions"))
admin.add_view(AdminModelView(ReplayRating, db.session, category="User actions"))
admin.add_view(AdminModelView(ReplayDownload, db.session, category="User actions"))

# Init admin
admin.init_app(app)


# Setup logging
import logging
app.logger.setLevel(logging.INFO)  # Set root logger to handle anything info and above

# Database logging for warnings
from app.handlers import SQLAlchemyHandler
db_handler = SQLAlchemyHandler()
db_handler.setLevel(logging.INFO)
app.logger.addHandler(db_handler)
