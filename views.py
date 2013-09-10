from flask import render_template, flash, redirect, request, url_for

from app import app, oid, steam, db, login_manager
from models import *
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
    latest_replays = Replay.query.limit(app.config["LATEST_REPLAYS_LIMIT"]).all()
    all_users = User.query.all()
    return render_template("dotabank.html", latest_replays=latest_replays, all_users=all_users)


@app.route("/user/<int:_id>/")
def user(_id):
    user = User.query.filter(User.id == _id).first()
    if user is None:
        flash("User {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))
    return render_template("user.html", user=user)


@app.route("/replays/")
@app.route("/replays/<int:page>/")
def replays(page=1):
    replays = Replay.query.paginate(page, app.config["REPLAYS_PER_PAGE"], False)
    return render_template("replays.html", replays=replays)


@app.route("/replay/<int:_id>/")
def replay(_id):
    replay = Replay.query.filter(Replay.id == _id).first()
    if replay is None:
        flash("Replay {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))
    return render_template("replay.html", replay=replay)

@app.route("/replay/<int:_id>/rate/")
@login_required
def replay_rate(_id):
    if "positive" in request.args:
        current_rating = ReplayRating.query.filter(ReplayRating.replay_id == _id, ReplayRating.user_id == current_user.id).first() or ReplayRating()
        try:
            positive_arg = bool(int(request.args["positive"]))

            current_rating.positive = positive_arg
            current_rating.user_id = current_user.id
            current_rating.replay_id = _id

            db.session.add(current_rating)
            db.session.commit()
        except TypeError:
            flash("There was a problem saving your rating!", "danger")
        return redirect(request.referrer or url_for("index"))
    else:
        flash("There was a problem saving your rating!", "danger")
        return redirect(request.referrer or url_for("index"))


@app.route("/replay/<int:_id>/favourite/")
@login_required
def replay_favourite(_id):
    favourite = ReplayFavourite.query.filter(ReplayFavourite.replay_id == _id, ReplayFavourite.user_id == current_user.id).first()
    try:
        if "remove" not in request.args or not bool(int(request.args["remove"])):
            if favourite is None:
                favourite = ReplayFavourite()
            favourite.user_id = current_user.id
            favourite.replay_id = _id

            db.session.add(favourite)
            db.session.commit()
        elif favourite is not None:
            db.session.delete(favourite)
            db.session.commit()
    except TypeError:
        flash("There was a problem favouriting {}!".format(_id), "danger")
    return redirect(request.referrer or url_for("index"))


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
