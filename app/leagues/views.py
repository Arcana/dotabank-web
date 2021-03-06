from flask import Blueprint, render_template, current_app, abort
from app.replays.models import Replay
from app import db, mem_cache
from models import League, LeagueView
from sqlalchemy.orm.exc import NoResultFound
from app.admin.views import AdminModelView

mod = Blueprint("leagues", __name__, url_prefix="/leagues")


@mem_cache.cached(timeout=60 * 60, key_prefix="leagues_data")
def _leagues_data():
    _leagues_and_count = db.session.query(
        League,
        db.func.count(Replay.id)
    ).\
        group_by(League.id).\
        filter(Replay.league_id == League.id).\
        order_by(db.func.count(Replay.id).desc()).\
        all()

    _leagues = []
    for _league, count in _leagues_and_count:
        _league.count = count
        _leagues.append(_league)

    return _leagues


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
    _league = League.query.get(_id)
    _view = None

    if _league is None:
        abort(404)

    if view is None:
        _replays = _league.replays.\
            order_by(Replay.id.desc()).\
            paginate(page, current_app.config["REPLAYS_PER_PAGE"], False)
    else:
        try:
            _view = LeagueView.query.filter(LeagueView.id == view, LeagueView.league_id == _id).one()
        except NoResultFound:
            abort(404)

        _replays = _league.replays.filter(*_view.get_filters()).\
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

class LeagueAdmin(AdminModelView):
    column_display_pk = True

    def __init__(self, session, **kwargs):
        # Just call parent class with predefined model.
        super(LeagueAdmin, self).__init__(League, session, **kwargs)