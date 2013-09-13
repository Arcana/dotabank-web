from flask import Flask
from flask.ext.cache import Cache
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from flask.ext.sqlalchemy import SQLAlchemy
import steam

app = Flask(__name__)

app.config.from_pyfile("settings.py")

cache = Cache(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
oid = OpenID(app)

# Setup steamodd
steam.api.key.set(app.config['STEAM_API_KEY'])
steam.api.socket_timeout.set(10)

from admin import admin
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
