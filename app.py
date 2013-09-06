from flask import Flask
from flask.ext.cache import Cache
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.debugtoolbar import DebugToolbarExtension
from flask.ext.admin import Admin

import steam

app = Flask(__name__)

app.config.from_pyfile("settings.py")

cache = Cache(app)
oid = OpenID(app)
login_manager = LoginManager(app)

db = SQLAlchemy(app)
toolbar = DebugToolbarExtension(app)

# Setup steamodd
steam.api.key.set(app.config['STEAM_API_KEY'])
steam.api.socket_timeout.set(10)

admin = Admin(app, name="Dotabank")

from models import *
