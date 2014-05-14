from flask import Blueprint, render_template, current_app, abort
from app.replays.models import Replay
from app import db, cache
from models import League
from sqlalchemy.sql import text


mod = Blueprint("leagues", __name__, url_prefix="/leagues")


@cache.cached(timeout=60 * 60)
def _leagues_data():
    _leagues = League.get_all()

    replay_counts = {x.league_id: x.count for x in db.engine.execute(
        text("""
            SELECT
                r.league_id as league_id,
                count(*) as count
            FROM {replay_table} r
            WHERE
                r.league_id in ({league_id_csv}) AND
                r.state = "ARCHIVED"
            GROUP BY r.league_id
            """.format(replay_table=Replay.__tablename__, league_id_csv=",".join(str(x.id) for x in _leagues))
        )
    )}

    leagues_with_replays = []
    for _league in _leagues:
        if replay_counts.get(_league.id) > 0:
            _league.count = replay_counts.get(_league.id)
            leagues_with_replays.append(_league)

    # Sort by archived count
    return sorted(leagues_with_replays, key=lambda r: r.count, reverse=True)


@mod.route("/")
def leagues():
    _leagues = _leagues_data()
    return render_template("leagues/leagues.html",
                           title="Leagues - Dotabank",
                           leagues=_leagues)


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
