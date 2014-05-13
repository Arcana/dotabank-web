from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app, abort
from app.replays.models import Replay
from app import cache
from models import League


mod = Blueprint("leagues", __name__, url_prefix="/leagues")


@mod.route("/")
@cache.cached(timeout=60 * 60)
def leagues():
    _leagues = League.get_all()

    leagues_with_replays = []
    for _league in _leagues:
        _league.count = Replay.query.filter(Replay.league_id == _league.id, Replay.state == "ARCHIVED").count()
        if _league.count > 0:
            leagues_with_replays.append(_league)

    # Sort by archived count
    leagues_with_replays = sorted(leagues_with_replays, key=lambda r: r.count, reverse=True)

    return render_template("leagues/leagues.html",
                           title="Leagues - Dotabank",
                           leagues=leagues_with_replays)


@mod.route("/<int:_id>/")
@mod.route("/<int:_id>/page/<int:page>")
def league(_id, page=1):
    _league = League.get_by_id(_id)
    if _league is None:
        abort(404)

    _replays = Replay.query.filter(Replay.league_id == _id, Replay.state == "ARCHIVED").paginate(page, current_app.config["REPLAYS_PER_PAGE"], False)

    return render_template("leagues/league.html",
                           title="{} - Dotabank".format(_league.name),
                           league=_league,
                           replays=_replays)
