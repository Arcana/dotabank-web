from flask import Flask
from flask.ext.cache import Cache
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from flask.ext.sqlalchemy import SQLAlchemy
import steam
from boto import sqs
from boto.s3.connection import S3Connection

app = Flask(__name__)
app.config.from_object("settings")

cache = Cache(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
oid = OpenID(app)

# Setup steamodd
steam.api.key.set(app.config['STEAM_API_KEY'])
steam.api.socket_timeout.set(10)

# Setup boto
sqs_connection = sqs.connect_to_region(
    app.config["AWS_REGION"],
    aws_access_key_id=app.config["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=app.config["AWS_SECRET_ACCESS_KEY"]
)

sqs_gc_queue = sqs_connection.create_queue("dotabank-gc")

s3_connection = S3Connection(
    aws_access_key_id=app.config["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=app.config["AWS_SECRET_ACCESS_KEY"]
)

dotabank_bucket = s3_connection.get_bucket(app.config["AWS_BUCKET"])

from views import index, about, internalerror


from app.admin.views import mod as admin_module
from app.users.views import mod as users_module
from app.replays.views import mod as replays_module

from app.admin.views import admin, AdminModelView
from app.users.views import UserAdmin
from app.replays.views import ReplayAdmin
from app.gc.views import GCWorkerAdmin


app.register_blueprint(admin_module)
app.register_blueprint(users_module)
app.register_blueprint(replays_module)

admin.add_view(UserAdmin(db.session, category="Models"))
admin.add_view(ReplayAdmin(db.session, category="Models"))
admin.add_view(GCWorkerAdmin(db.session, category="Models"))

admin.init_app(app)

# Debug environment
if app.debug:
    from flask.ext.debugtoolbar import DebugToolbarExtension
    toolbar = DebugToolbarExtension(app)

# Production environment code
else:
    import logging
    from logging.handlers import SMTPHandler
    credentials = None
    if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
        credentials = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
    mail_handler = SMTPHandler((app.config["MAIL_SERVER"], app.config["MAIL_PORT"]), 'no-reply@' + app.config["MAIL_SERVER"], app.config["ADMINS"], 'dotabank failure', credentials)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
