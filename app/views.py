from flask import render_template

from app import app, db
from app.users.models import User
from app.replays.models import Replay

from flask.ext.login import current_user
from flask.ext.admin import expose
from flask.ext.admin import AdminIndexView
from flask.ext.admin.contrib.sqlamodel import ModelView


# Routes
@app.route('/')
def index():
    latest_replays = Replay.query.limit(app.config["LATEST_REPLAYS_LIMIT"]).all()
    all_users = User.query.all()
    return render_template("dotabank.html", latest_replays=latest_replays, all_users=all_users)


@app.route("/about/")
def about():
    return render_template("about.html", emule=app.config["CONTACT_EMAIL"])


@app.errorhandler(401)  # Unauthorized
@app.errorhandler(403)  # Forbidden
@app.errorhandler(404)  # > Missing middle!
@app.errorhandler(500)  # Internal server error.
def internalerror(error):
    if error.code == 401:
        error.description = "I'm sorry Dave, I'm afraid I can't do that.  Try logging in."
    elif error.code == 403:
        if current_user.is_authenticated():
            error.description = "I'm sorry {{ current_user.name }}, I'm afraid I can't do that.  You do not have access to this resource.</p>"
        else:
            error.description = "Hacker."
    elif error.code == 500:
        db.session.rollback()
    return render_template("error.html", error=error, title=error.name), error.code


class AuthMixin(object):
    def is_accessible(self):
        return current_user.is_admin()


class AdminModelView(AuthMixin, ModelView):
    pass


class AdminIndex(AuthMixin, AdminIndexView):
    @expose("/")
    def index(self):
        return self.render('admin/index.html')
