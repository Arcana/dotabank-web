from flask import Flask
from flask.ext.cache import Cache
from flask.ext.openid import OpenID
from flask.ext.sqlalchemy import SQLAlchemy
import steam

app = Flask(__name__)

app.config.from_pyfile("settings.py")

cache = Cache(app)
oid = OpenID(app)

db = SQLAlchemy(app)

# Setup steamodd
steam.api.key.set(app.config['STEAM_API_KEY'])
steam.api.socket_timeout.set(10)


# noinspection PyUnresolvedReferences
from views import *

if __name__ == '__main__':
    app.run()
