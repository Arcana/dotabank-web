from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app

from app import steam, db, cache
from models import Replay, ReplayRating, ReplayFavourite, CombatLogMessage
from flask.ext.login import current_user, login_required
from app.admin.views import AdminModelView
from filters import get_hero_by_id, get_hero_by_name

mod = Blueprint("replays", __name__, url_prefix="/replays")

mod.add_app_template_filter(get_hero_by_id)
mod.add_app_template_filter(get_hero_by_name)

@mod.route("/")
@mod.route("/page/<int:page>/")
def replays(page=1):
    # TODO: Filters & ordering
    replays = Replay.query.paginate(page, current_app.config["REPLAYS_PER_PAGE"], False)
    return render_template("replays/replays.html", replays=replays)


@mod.route("/<int:_id>/")
def replay(_id):
    replay = Replay.query.filter(Replay.id == _id).first()
    if replay is None:
        flash("Replay {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    return render_template("replays/replay.html", replay=replay)


@mod.route("/<int:_id>/combatlog/")
@mod.route("/<int:_id>/combatlog/<int:page>/")
@cache.cached(timeout=60 * 60)  # 1hr
def combatlog(_id, page=1):
    # TODO: Search for tick / timestamp and redirect to appropriate page.
    replay = Replay.query.filter(Replay.id == _id).first()
    if replay is None:
        flash("Replay {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    combatlog = replay.combatlog.paginate(page, current_app.config["COMBATLOG_MSGS_PER_PAGE"], False)

    if len(combatlog.items) == 0:
        flash("Motherfucking fuckers fucking my fuckfactory.", "danger")
        return redirect(request.referrer or url_for("index"))

    return render_template("replays/combatlog.html", replay=replay, combatlog=combatlog)


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

@mod.route("/search/")
def search():
    match_id = request.args.get("id")
    if unicode.isdecimal(unicode(match_id)):
        replay = Replay.query.filter(Replay.id == match_id).first()

        # If we don't have match_id in database, check if it's a valid match via the WebAPI and if so add it to DB.
        if not replay and "error" not in steam.api.interface("IDOTA2Match_570").GetMatchDetails(match_id=match_id).get("result").keys():
            flash("Replay {} was not in our database, so we've added it to the job queue to be parsed! AINT WE NICE?".format(match_id), "info")
            replay = Replay(match_id)
            db.session.add(replay)
            db.session.commit()

        if replay:
            return redirect(url_for("replays.replay", _id=match_id))

    # Only invalid matches make it this far!
    flash("Invalid match id.  If this match id corresponds to a practice match it is also interpreted as invalid - Dotabank is unable to access practice lobby replays.", "danger")
    return redirect(request.referrer or url_for("index"))


class ReplayAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ("id", "url", "state", "replay_state")

    def __init__(self, session, **kwargs):
        # Just call parent class with predefined model.
        super(ReplayAdmin, self).__init__(Replay, session, **kwargs)
