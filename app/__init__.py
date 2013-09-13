from flask import Flask
from flask.ext.admin import Admin
from flask.ext.cache import Cache
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from flask.ext.sqlalchemy import SQLAlchemy
import steam

app = Flask(__name__)
app.config.from_object("settings")

cache = Cache(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
oid = OpenID(app)

admin = Admin(app, name="Dotabank")
from views import index, about, internalerror, AdminModelView

# Setup steamodd
steam.api.key.set(app.config['STEAM_API_KEY'])
steam.api.socket_timeout.set(10)

from app.users.views import mod as usersModule
from app.users.views import UserAdmin
from app.replays.views import mod as replaysModule
from app.replays.views import ReplayAdmin
from app.replays.models import ReplayRating, ReplayFavourite
from app.gc.views import GCWorkerAdmin
from app.gc.models import GCJob

app.register_blueprint(usersModule)
app.register_blueprint(replaysModule)

admin.add_view(UserAdmin(db.session))
admin.add_view(ReplayAdmin(db.session, category='Replays'))
admin.add_view(AdminModelView(ReplayRating, db.session, category='Replays'))
admin.add_view(AdminModelView(ReplayFavourite, db.session, category='Replays'))
admin.add_view(GCWorkerAdmin(db.session, category='GC'))
admin.add_view(AdminModelView(GCJob, db.session, category='GC'))

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
