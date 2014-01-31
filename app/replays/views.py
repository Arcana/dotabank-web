from itertools import groupby
import operator
from datetime import datetime, timedelta

from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app
from flask.ext.login import current_user, login_required

from app import steam, db, dotabank_bucket
from models import Replay, ReplayRating, ReplayFavourite, ReplayDownload, Search
from app.admin.views import AdminModelView
from app.filters import get_hero_by_id, get_hero_by_name, get_item_by_id, get_league_by_id
from forms import DownloadForm, SearchForm


mod = Blueprint("replays", __name__, url_prefix="/replays")

mod.add_app_template_filter(get_hero_by_id)
mod.add_app_template_filter(get_hero_by_name)
mod.add_app_template_filter(get_item_by_id)
mod.add_app_template_filter(get_league_by_id)


@mod.route("/")
@mod.route("/page/<int:page>/")
def replays(page=1):
    # TODO: Filters & ordering
    _replays = Replay.query.order_by(Replay.added_to_site_time.desc()).paginate(page, current_app.config["REPLAYS_PER_PAGE"], False)
    return render_template("replays/replays.html", replays=_replays)


@mod.route("/<int:_id>/")
def replay(_id):
    _replay = Replay.query.filter(Replay.id == _id).first()
    if _replay is None:
        return redirect(url_for("replays.search", id=_id))

    building_statuses = ["{0:011b}".format(_replay.radiant_tower_status), "{0:011b}".format(_replay.dire_tower_status),
                         "{0:06b}".format(_replay.radiant_barracks_status), "{0:06b}".format(_replay.dire_barracks_status)]
    return render_template("replays/replay.html", replay=_replay, building_statuses=building_statuses, api_key=current_app.config["STEAM_API_KEY"])


@mod.route("/<int:_id>/rate/")
@login_required
def replay_rate(_id):
    # TODO: API-ify (ajax request & jsonify response)
    if "positive" in request.args:
        current_rating = ReplayRating.query.filter(ReplayRating.replay_id == _id, ReplayRating.user_id == current_user.get_id()).first() or ReplayRating()
        try:
            positive_arg = bool(int(request.args["positive"]))

            current_rating.positive = positive_arg
            current_rating.user_id = current_user.get_id()
            current_rating.replay_id = _id

            db.session.add(current_rating)
            db.session.commit()
        except TypeError:
            flash("There was a problem saving your rating!", "danger")
        return redirect(request.referrer or url_for("index"))
    else:
        flash("There was a problem saving your rating!", "danger")
        return redirect(request.referrer or url_for("index"))


@mod.route("/<int:_id>/add_gc_job")
@login_required
def add_gc_job(_id):
    # Check auth
    if not current_user.is_admin():
        flash("Only admins can add new GC jobs.", "danger")
        return redirect(request.referrer or url_for("index"))

    # Check replay exists
    _replay = Replay.query.filter(Replay.id == _id).first()
    if _replay is None:
        flash("Replay {} doesn't exist.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    # Update status
    _replay.status = "WAITING_GC"
    db.session.add(_replay)

    # Add to job queue.
    queued = Replay.add_gc_job(_replay)
    if queued:
        flash("Added GC job for replay {}.".format(_id), "info")
        db.session.commit()
    else:
        flash("Error adding GC job for replay {}.".format(_id), "danger")
        db.session.rollback()

    return redirect(request.referrer or url_for("index"))


@mod.route("/<int:_id>/add_dl_job")
@login_required
def add_dl_job(_id):
    # Check auth
    if not current_user.is_admin():
        flash("Only admins can add new DL jobs.", "danger")
        return redirect(request.referrer or url_for("index"))

    # Check replay exists
    _replay = Replay.query.filter(Replay.id == _id).first()
    if _replay is None:
        flash("Replay {} doesn't exist.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    # Update status
    _replay.status = "WAITING_DOWNLOAD"
    db.session.add(_replay)

    # Add to job queue.
    queued = Replay.add_dl_job(_replay)
    if queued:
        flash("Added DL job for replay {}.".format(_id), "info")
        db.session.commit()
    else:
        flash("Error adding DL job for replay {}.".format(_id), "danger")
        db.session.rollback()

    return redirect(request.referrer or url_for("index"))



@mod.route("/<int:_id>/favourite/")
@login_required
def replay_favourite(_id):
    # TODO: API-ify (ajax request & jsonify response)
    favourite = ReplayFavourite.query.filter(ReplayFavourite.replay_id == _id, ReplayFavourite.user_id == current_user.get_id()).first()
    try:
        if "remove" not in request.args or not bool(int(request.args["remove"])):
            if favourite is None:
                favourite = ReplayFavourite()
            favourite.user_id = current_user.get_id()
            favourite.replay_id = _id

            db.session.add(favourite)
            db.session.commit()
        elif favourite is not None:
            db.session.delete(favourite)
            db.session.commit()
    except TypeError:
        flash("There was a problem favouriting {}!".format(_id), "danger")
    return redirect(request.referrer or url_for("index"))


@mod.route("/<int:_id>/download/", methods=['GET', 'POST'])
@login_required
def download(_id):
    _replay = Replay.query.filter(Replay.id == _id).first()
    if _replay is None:
        flash("Replay {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    if _replay.local_uri is None:
        flash("Replay {} not yet stored in Dotabank.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    form = DownloadForm()
    key = dotabank_bucket.get_key(_replay.local_uri)

    expires_at = (datetime.utcnow() + timedelta(seconds=current_app.config["REPLAY_DOWNLOAD_TIMEOUT"])).ctime()
    name = key.name
    md5 = key.etag.replace("\"", "")
    filesize = key.size
    if form.validate_on_submit():
        url = key.generate_url(current_app.config["REPLAY_DOWNLOAD_TIMEOUT"])

        download_log_entry = ReplayDownload(
            _replay.id,
            current_user.get_id() if current_user else None
        )
        db.session.add(download_log_entry)
        db.session.commit()

        return render_template("replays/download_granted.html",
                               replay=_replay,
                               expires_at=expires_at,
                               name=name,
                               md5=md5,
                               filesize=filesize,
                               url=url)

    return render_template("replays/download.html",
                           replay=_replay,
                           name=name,
                           md5=md5,
                           filesize=filesize,
                           form=form)


@mod.route("/search/", methods=['POST'])
def search():
    form = SearchForm()

    if form.validate_on_submit():
        match_id = form.query.data
        error = False

        search_log = Search(current_user.get_id(), match_id, request.access_route[0])

        if unicode.isdecimal(unicode(match_id)):
            _replay = Replay.query.filter(Replay.id == match_id).first()

            # If we don't have match_id in database, check if it's a valid match via the WebAPI and if so add it to DB.
            if not _replay:
                try:
                    matchDetails = steam.api.interface("IDOTA2Match_570").GetMatchDetails(match_id=match_id).get("result")
                    if "error" not in matchDetails.keys():
                        _replay = Replay(match_id)
                        _replay.game_mode = matchDetails.get("game_mode")
                        db.session.add(_replay)

                        queued = Replay.add_gc_job(_replay)
                        if queued:
                            flash("Replay {} was not in our database, so we've added it to the job queue to be parsed!".format(match_id), "info")
                            db.session.commit()
                        else:
                            db.session.rollback()
                            error = True
                except steam.api.HTTPError:
                    error = True

            if _replay:
                search_log.replay_id = _replay.id
                search_log.success = True
                db.session.add(search_log)
                db.session.commit()
                return redirect(url_for("replays.replay", _id=match_id))

        # We only get this far if there was an error or the matchid is invalid.
        if error:
            flash("Replay {} was not on our database, and we encountered errors trying to add it.  Please try again later.".format(match_id), "warning")
        else:
            flash("Invalid match id.  If this match id corresponds to a practice match it is also interpreted as invalid - Dotabank is unable to access practice lobby replays.", "danger")

        search_log.success = False
        db.session.add(search_log)
        db.session.commit()
    return redirect(request.referrer or url_for("index"))


class ReplayAdmin(AdminModelView):
    column_display_pk = True

    def __init__(self, session, **kwargs):
        # Just call parent class with predefined model.
        super(ReplayAdmin, self).__init__(Replay, session, **kwargs)
