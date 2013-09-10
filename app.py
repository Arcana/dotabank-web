from flask import Flask
from flask.ext.cache import Cache
from flask.ext.login import LoginManager, current_user
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

# Debug environment
if app.debug:
    from flask.ext.debugtoolbar import DebugToolbarExtension
    from flask.ext.admin import Admin
    from flask.ext.admin.contrib.sqlamodel import ModelView
    from models import User, Replay, ReplayRating, ReplayFavourite, GCWorker, GCJob

    toolbar = DebugToolbarExtension(app)
    admin = Admin(name="Dotabank")

    class AdminModelView(ModelView):
        def is_accessible(self):
            return current_user.is_authenticated()

    class UserAdmin(AdminModelView):
        column_display_pk = True
        form_columns = ('id', 'name', 'enabled')

        def __init__(self, session):
            # Just call parent class with predefined model.
            super(UserAdmin, self).__init__(User, session)

    class ReplayAdmin(AdminModelView):
        column_display_pk = True
        form_columns = ("id", "url", "state", "replay_state")

        def __init__(self, session):
            # Just call parent class with predefined model.
            super(ReplayAdmin, self).__init__(Replay, session)

    admin.add_view(UserAdmin(db.session))
    admin.add_view(ReplayAdmin(db.session))
    admin.add_view(AdminModelView(ReplayRating, db.session))
    admin.add_view(AdminModelView(ReplayFavourite, db.session))
    admin.add_view(AdminModelView(GCWorker, db.session))
    admin.add_view(AdminModelView(GCJob, db.session))

    admin.init_app(app)


# Production environment code
else:
    import logging
    from logging.handlers import SMTPHandler
    credentials = None
    if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
        credentials = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
    mail_handler = SMTPHandler((app.config["MAIL_SERVER"], app.config["MAIL_PORT"]), 'no-reply@' + app.config["MAIL_SERVER"], app.config["ADMINS"], 'microblog failure', credentials)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
