from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app
from itertools import groupby
import operator
from datetime import datetime, timedelta

from app import steam, db, sqs_gc_queue, dotabank_bucket
from models import Replay, ReplayRating, ReplayFavourite, ReplayDownload
from flask.ext.login import current_user, login_required
from app.admin.views import AdminModelView
from filters import get_hero_by_id, get_hero_by_name
from forms import DownloadForm
from boto.sqs.message import RawMessage as sqsMessage

mod = Blueprint("replays", __name__, url_prefix="/replays")

mod.add_app_template_filter(get_hero_by_id)
mod.add_app_template_filter(get_hero_by_name)

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
        flash("Replay {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    graph_data = _replay.players.all()
    if graph_data:
        graph_data = sorted(graph_data, key=operator.attrgetter("team"))
        graph_labels = [int(y.tick) for y in max(graph_data, key=lambda x: len(x.player_snapshots)).player_snapshots]
    else:
        graph_labels = None

    teams = {}
    teams_delta = {}  # Key: Tick
    for key, vals in groupby(graph_data, key=operator.attrgetter("team")):
        players = list(vals)

        teams[key] = {}  # Key: tick
        for player in players:
            for snapshot in player.player_snapshots:
                if teams[key].get(snapshot.tick) is None:
                    teams[key][snapshot.tick] = {
                        "tick": snapshot.tick,
                        "gold": 0,
                        "exp": 0,
                        "lh": 0,
                        "dn": 0,
                        "kills": 0,
                        "deaths": 0,
                        "assists": 0,
                        "max_hp": 0,
                        "max_mana": 0,
                        "str": 0,
                        "int": 0,
                        "agi": 0
                    }
                if teams_delta.get(snapshot.tick) is None:
                    teams_delta[snapshot.tick] = {
                        "tick": snapshot.tick,
                        "gold": 0,
                        "exp": 0,
                        "lh": 0,
                        "dn": 0,
                        "kills": 0,
                        "deaths": 0,
                        "assists": 0,
                        "max_hp": 0,
                        "max_mana": 0,
                        "str": 0,
                        "int": 0,
                        "agi": 0
                    }

                teams[key][snapshot.tick]["gold"] += snapshot.earned_gold
                teams[key][snapshot.tick]["exp"] += snapshot.xp
                teams[key][snapshot.tick]["lh"] += snapshot.last_hits
                teams[key][snapshot.tick]["dn"] += snapshot.denies
                teams[key][snapshot.tick]["kills"] += snapshot.kills
                teams[key][snapshot.tick]["deaths"] += snapshot.deaths
                teams[key][snapshot.tick]["assists"] += snapshot.assists
                teams[key][snapshot.tick]["max_hp"] += snapshot.max_health
                teams[key][snapshot.tick]["max_mana"] += snapshot.max_mana
                teams[key][snapshot.tick]["str"] += snapshot.strength
                teams[key][snapshot.tick]["int"] += snapshot.intelligence
                teams[key][snapshot.tick]["agi"] += snapshot.agility

                if key == "radiant":
                    teams_delta[snapshot.tick]["gold"] += snapshot.earned_gold
                    teams_delta[snapshot.tick]["exp"] += snapshot.xp
                    teams_delta[snapshot.tick]["lh"] += snapshot.last_hits
                    teams_delta[snapshot.tick]["dn"] += snapshot.denies
                    teams_delta[snapshot.tick]["kills"] += snapshot.kills
                    teams_delta[snapshot.tick]["deaths"] += snapshot.deaths
                    teams_delta[snapshot.tick]["assists"] += snapshot.assists
                    teams_delta[snapshot.tick]["max_hp"] += snapshot.max_health
                    teams_delta[snapshot.tick]["max_mana"] += snapshot.max_mana
                    teams_delta[snapshot.tick]["str"] += snapshot.strength
                    teams_delta[snapshot.tick]["int"] += snapshot.intelligence
                    teams_delta[snapshot.tick]["agi"] += snapshot.agility
                elif key == "dire":
                    teams_delta[snapshot.tick]["gold"] -= snapshot.earned_gold
                    teams_delta[snapshot.tick]["exp"] -= snapshot.xp
                    teams_delta[snapshot.tick]["lh"] -= snapshot.last_hits
                    teams_delta[snapshot.tick]["dn"] -= snapshot.denies
                    teams_delta[snapshot.tick]["kills"] -= snapshot.kills
                    teams_delta[snapshot.tick]["deaths"] -= snapshot.deaths
                    teams_delta[snapshot.tick]["assists"] -= snapshot.assists
                    teams_delta[snapshot.tick]["max_hp"] -= snapshot.max_health
                    teams_delta[snapshot.tick]["max_mana"] -= snapshot.max_mana
                    teams_delta[snapshot.tick]["str"] -= snapshot.strength
                    teams_delta[snapshot.tick]["int"] -= snapshot.intelligence
                    teams_delta[snapshot.tick]["agi"] -= snapshot.agility

    return render_template("replays/replay.html", replay=_replay, graph_data=graph_data, graph_labels=graph_labels, graph_teams=teams, graph_teams_delta=teams_delta)


@mod.route("/<int:_id>/combatlog/")
@mod.route("/<int:_id>/combatlog/<int:page>/")
def combatlog(_id, page=1):
    # TODO: Search for tick / timestamp and redirect to appropriate page.
    _replay = Replay.query.filter(Replay.id == _id).first()
    if _replay is None:
        flash("Replay {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    _combatlog = _replay.combatlog.paginate(page, current_app.config["COMBATLOG_MSGS_PER_PAGE"], False)

    if len(_combatlog.items) == 0:
        flash("Motherfucking fuckers fucking my fuckfactory.", "danger")
        return redirect(request.referrer or url_for("index"))
    return render_template("replays/combatlog.html", replay=_replay, combatlog=_combatlog)


@mod.route("/<int:_id>/rate/")
@login_required
def replay_rate(_id):
    # TODO: API-ify (ajax request & jsonify response)
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


@mod.route("/<int:_id>/favourite/")
@login_required
def replay_favourite(_id):
    # TODO: API-ify (ajax request & jsonify response)
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
            current_user.id if current_user else None
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


@mod.route("/search/")
def search():
    match_id = request.args.get("id")
    if unicode.isdecimal(unicode(match_id)):
        _replay = Replay.query.filter(Replay.id == match_id).first()

        # If we don't have match_id in database, check if it's a valid match via the WebAPI and if so add it to DB.
        if not _replay and "error" not in steam.api.interface("IDOTA2Match_570").GetMatchDetails(match_id=match_id).get("result").keys():
            flash("Replay {} was not in our database, so we've added it to the job queue to be parsed! AINT WE NICE?".format(match_id), "info")
            _replay = Replay(match_id)
            db.session.add(_replay)

            # Write to SQS
            msg = sqsMessage()
            msg.set_body(match_id)
            queued = sqs_gc_queue.write(msg)

            if queued:
                db.session.commit()
            else:
                db.rollback()
                _replay = None
                flash("Replay {} was not on our database, and we encountered errors trying to add it.  Please try again later.".format(match_id), "warning")

        if _replay:
            return redirect(url_for("replays.replay", _id=match_id))

    # Only invalid matches make it this far!
    flash("Invalid match id.  If this match id corresponds to a practice match it is also interpreted as invalid - Dotabank is unable to access practice lobby replays.", "danger")
    return redirect(request.referrer or url_for("index"))


class ReplayAdmin(AdminModelView):
    column_display_pk = True

    def __init__(self, session, **kwargs):
        # Just call parent class with predefined model.
        super(ReplayAdmin, self).__init__(Replay, session, **kwargs)
