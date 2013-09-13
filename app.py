from flask import Flask
from flask.ext.admin import Admin
from flask.ext.cache import Cache
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from flask.ext.sqlalchemy import SQLAlchemy
import steam

# Initialize everything here; it'll be loaded elsewhere.
app = Flask(__name__)
app.config.from_pyfile("settings.py")

admin = Admin(app, name="Dotabank")
cache = Cache(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
oid = OpenID(app)

# Setup steamodd
steam.api.key.set(app.config['STEAM_API_KEY'])
steam.api.socket_timeout.set(10)
