from flask import render_template, flash, redirect, session, g, request, jsonify

from app import app, oid, steam, db, login_manager, admin
from models import *

from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import login_user, logout_user, current_user, login_required


# User authentication

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)
    return user


@app.route('/login/')
@oid.loginhandler
def login():
    if current_user.is_authenticated():
        return redirect(oid.get_next_url())
    return oid.try_login('http://steamcommunity.com/openid')


@oid.after_login
def create_or_login(resp):
    steam_id = long(resp.identity_url.replace("http://steamcommunity.com/openid/id/", ""))
    account_id = int(steam_id & 0xFFFFFFFF)
    user = User.query.filter(User.id == int(account_id & 0xFFFFFFFF)).first()

    if not user:
        user = User(int(account_id & 0xFFFFFFFF), steam.user.profile(steam_id).persona or account_id)

        db.session.add(user)
        db.session.commit()

    login_attempt = login_user(user)
    if login_attempt is True:
        flash("You are logged in as {}".format(user.name), "success")
    elif not user.is_active():
        flash("Cannot log you in as {}, your account has been disabled.  If you believe this is in error, please contact {}.".format(user.name, app.config["CONTACT_EMAIL"]), "danger")
    else:
        flash("Error logging you in as {}, please try again later.".format(user.name), "danger")
    return redirect(oid.get_next_url())


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(oid.get_next_url())


# Routes
@app.route('/')
def index():
    latest_replays = Replay.query.limit(64).all()

    return render_template("dotabank.html", latest_replays=latest_replays)


@app.route("/user/<int:_id>")
def user(_id):
    return _id


@app.route("/replay/<int:_id>")
def replay(_id):
    replay = Replay.query.filter(Replay.id == _id).first_or_404()
    return render_template("replay.html", replay=replay)

@app.route("/replay/<int:_id>/rate")
@login_required
def replay_rate(_id):
    current_rating = ReplayRating.query.filter(ReplayRating.replay_id == _id, ReplayRating.user_id == current_user.id).first() or ReplayRating()
    if "positive" in request.args:
        try:
            positive_arg = bool(int(request.args["positive"]))

            current_rating.positive = positive_arg
            current_rating.user_id = current_user.id
            current_rating.replay_id = _id

            db.session.add(current_rating)
            db.session.commit()
        except TypeError:
            flash("There was a problem saving your rating!", "error")
        return redirect(request.referrer)
    else:
        flash("There was a problem saving your rating!", "error")
        return redirect(request.referrer)


# Admin views

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


class ReplayRatingAdmin(AdminModelView):
    def __init__(self, session):
        # Just call parent class with predefined model.
        super(ReplayRatingAdmin, self).__init__(ReplayRating, session)


admin.add_view(UserAdmin(db.session))
admin.add_view(ReplayAdmin(db.session))
admin.add_view(ReplayRatingAdmin(db.session))
