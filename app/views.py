from flask import render_template
from datetime import datetime, timedelta

from app import app, db
from app.models import Stats
from app.users.models import User
from app.replays.models import Replay
from app.replays.models import ReplayDownload
from app.replays.forms import SearchForm


from flask.ext.login import current_user


# Inject search form into template (CSRF)
@app.context_processor
def inject_search_form():
    return dict(search_form=SearchForm())


# Routes
@app.route('/')
def index():
    last_added_replays = Replay.query.order_by(Replay.added_to_site_time.desc()).limit(app.config["LATEST_REPLAYS_LIMIT"]).all()
    last_archived_replays = Replay.query.filter(Replay.state == "ARCHIVED").order_by(Replay.dl_done_time.desc()).limit(app.config["LATEST_REPLAYS_LIMIT"]).all()

    stats = Stats()

    search_form = SearchForm()

    return render_template("dotabank.html",
                           last_added_replays=last_added_replays,
                           last_archived_replays=last_archived_replays,
                           stats=stats,
                           search_form=search_form)


@app.route("/privacy/")
def privacy():
    return render_template("privacy.html")


@app.route("/tos/")
def tos():
    return render_template("tos.html")


@app.route("/about/")
def about():
    return render_template("about.html")


@app.errorhandler(401)  # Unauthorized
@app.errorhandler(403)  # Forbidden
@app.errorhandler(404)  # > Missing middle!
@app.errorhandler(500)  # Internal server error.
# @app.errorhandler(Exception)  # Internal server error.
def internalerror(error):
    try:
        if error.code == 401:
            error.description = "I'm sorry Dave, I'm afraid I can't do that.  Try logging in."
        elif error.code == 403:
            if current_user.is_authenticated():
                error.description = "I'm sorry {{ current_user.name }}, I'm afraid I can't do that.  You do not have access to this resource.</p>"
            else:
                error.description = "Hacker."
    except AttributeError:
        db.session.rollback()
        error.code = 500
        error.name = "Internal Server Error"
        error.description = "Whoops! Something went wrong server-side.  Details of the problem has been sent to the Dotabank team for investigation."
    return render_template("error.html", error=error, title=error.name), error.code
