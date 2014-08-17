from flask import Blueprint, render_template, current_app, abort
from app.replays.models import Replay, ReplayDownload
from app import db, mem_cache, sentry
from models import League, LeagueView
from sqlalchemy.sql import text
from sqlalchemy.orm.exc import NoResultFound

mod = Blueprint("leagues", __name__, url_prefix="/leagues")


@mem_cache.cached(timeout=10 * 60, key_prefix="leagues_data")  # Cache data for 10 minutes
def _leagues_data():
    _leagues = League.get_all()

    if len(_leagues) == 0:
        sentry.captureMessage('Leagues.get_all() returned an empty list.')
        return []

    replay_counts = {x.league_id: x.count for x in db.engine.execute(
        text("""
            SELECT
                r.league_id as league_id,
                count(*) as count
            FROM {replay_table} r
            WHERE
                r.state = "ARCHIVED"
            GROUP BY r.league_id
            """.format(replay_table=Replay.__tablename__)
        )
    )}

    download_counts = {x.league_id: x.count for x in db.engine.execute(
        text("""
            SELECT
                rp.league_id as league_id,
                count(rd.id) as count
            FROM {replay_download_table} rd
            LEFT JOIN {replay_table} rp ON rp.id = rd.replay_id
            WHERE
                rp.state = "ARCHIVED"
            GROUP BY rp.league_id
            """.format(replay_table=Replay.__tablename__, replay_download_table=ReplayDownload.__tablename__)
        )
    )}

    leagues_with_replays = []
    for _league in _leagues:
        if replay_counts.get(_league.id) > 0:
            _league.replay_count = replay_counts.get(_league.id)
            _league.download_count = download_counts.get(_league.id)
            leagues_with_replays.append(_league)

    # Sort by archived count
    return sorted(leagues_with_replays, key=lambda r: r.download_count, reverse=True)


@mod.route("/")
def leagues():
    _leagues = _leagues_data()
    return render_template("leagues/leagues.html",
                           title="Leagues - Dotabank",
                           leagues=_leagues)


@mod.route("/<int:_id>/")
@mod.route("/<int:_id>/page/<int:page>")
@mod.route("/<int:_id>/<int:view>")
@mod.route("/<int:_id>/<int:view>/page/<int:page>")
def league(_id, view=None, page=1):
    _league = League.get_by_id(_id)
    _view = None

    if _league is None:
        abort(404)

    if view is None:
        _replays = Replay.query.filter(Replay.league_id == _id).\
            order_by(Replay.id.desc()).\
            paginate(page, current_app.config["REPLAYS_PER_PAGE"], False)
    else:
        try:
            _view = LeagueView.query.filter(LeagueView.id == view, LeagueView.league_id == _id).one()
        except NoResultFound:
            abort(404)

        _replays = Replay.query.filter(Replay.league_id == _id, *_view.get_filters()).\
            order_by(Replay.id.desc()).\
            paginate(page, current_app.config["REPLAYS_PER_PAGE"], False)

    # Get all views
    views = LeagueView.query.filter(LeagueView.league_id == _id).all()

    return render_template("leagues/league.html",
                           title=u"{} - Dotabank".format(_league.name),
                           meta_description=u"Replays archived for {}; {} ...".format(_league.name, _league.short_description),
                           league=_league,
                           replays=_replays,
                           current_view=_view,
                           page=page,
                           views=views)
