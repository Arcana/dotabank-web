from flask import render_template
from datetime import datetime, timedelta

from app import app, db
from app.users.models import User
from app.replays.models import Replay
from app.replays.models import ReplayDownload
from app.gc.models import GCJob

from flask.ext.login import current_user

# Routes
@app.route('/')
def index():
    last_added_replays = Replay.query.order_by(Replay.added_to_site_time.desc()).limit(app.config["LATEST_REPLAYS_LIMIT"]).all()
    last_archived_replays = Replay.query.filter(Replay.state == "ARCHIVED").order_by(Replay.dl_done_time.desc()).limit(app.config["LATEST_REPLAYS_LIMIT"]).all()

    stats = {
        'total': {
            'replays': Replay.query.count(),
            'archived': Replay.query.filter(Replay.local_uri != None).count(),  # Have to use != instead of 'is not' here, because sqlalchemy.
            'users': User.query.count(),
            'downloads': ReplayDownload.query.count()
        }
    }
    for key, hours in [
        ("day", 24),
        ("week", 24 * 7),
        ("month", 24 * 30)
    ]:
        _time_ago = datetime.utcnow() - timedelta(hours=hours)
        stats[key] = {
            'replays': Replay.query.filter(Replay.added_to_site_time >= _time_ago).count(),
            'archived': Replay.query.filter(Replay.local_uri != None,
                                            Replay.added_to_site_time >= _time_ago).count(),  # Have to use != instead of 'is not' here, because sqlalchemy.
            'users': User.query.filter(User.first_seen >= _time_ago).count(),
            'downloads': ReplayDownload.query.filter(ReplayDownload.created_at >= _time_ago).count()
        }

    return render_template("dotabank.html",
                           last_added_replays=last_added_replays,
                           last_archived_replays=last_archived_replays,
                           stats=stats)


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
