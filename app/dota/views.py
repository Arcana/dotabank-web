from flask import Blueprint, render_template, current_app, abort, g
from app.replays.models import Replay, ReplayPlayer
from app import db, mem_cache
from models import Hero

hero_mod = Blueprint("heroes", __name__, url_prefix="/heroes")


@hero_mod.before_app_request
def add_heroes_to_globals():
    g.all_heroes = sorted(Hero.get_all(), key=lambda h: h.name)


@mem_cache.cached(timeout=60 * 60, key_prefix="heroes_data")
def _heroes_data():
    hero_ids = [h.id for h in g.all_heroes]
    _heroes_and_count = db.session.query(
        ReplayPlayer.hero_id,
        db.func.count(ReplayPlayer.replay_id)
    ).\
        group_by(ReplayPlayer.hero_id).\
        filter(ReplayPlayer.hero_id.in_(hero_ids)).\
        order_by(db.func.count(ReplayPlayer.replay_id).desc()).\
        all()

    _heroes = []
    for hero_id, count in _heroes_and_count:
        _hero = Hero.get_by_id(hero_id)
        _hero.count = count
        _heroes.append(_hero)

    return _heroes


@hero_mod.route("/")
def heroes():
    _heroes = _heroes_data()
    return render_template("dota/heroes.html",
                           title="Heroes - Dotabank",
                           heroes=_heroes)


@hero_mod.route("/<string:_name>/")
@hero_mod.route("/<string:_name>/page/<int:page>")
def hero(_name, page=1):
    _hero = Hero.get_by_name(_name)

    if _hero is None:
        abort(404)

    # TODO: This is focken slow
    _replays = _hero.replays.\
        order_by(Replay.id.desc()).\
        paginate(page, current_app.config["REPLAYS_PER_PAGE"], False)

    return render_template("dota/hero.html",
                           title=u"{} - Dotabank".format(_hero.localized_name),
                           meta_description=u"Replays archived for {}".format(_hero.localized_name),
                           hero=_hero,
                           replays=_replays,
                           page=page)