from flask import Blueprint, render_template, current_app, abort, g
from sqlalchemy import distinct
from app.replays.models import Replay, ReplayPlayer
from app import db, mem_cache
from models import Hero

hero_mod = Blueprint("heroes", __name__, url_prefix="/heroes")

@hero_mod.before_app_request
def add_heroes_to_globals():
    g.all_heroes = Hero.query.order_by(Hero.name).all()

@hero_mod.route("/")
def heroes():
    _heroes_and_replay_counts = db.session.query(db.func.count(distinct(ReplayPlayer.replay_id)), Hero)\
        .join(ReplayPlayer.hero)\
        .group_by(ReplayPlayer.hero_id)\
        .order_by(db.func.count(distinct(ReplayPlayer.replay_id)).desc())\
        .all()

    return render_template("dota/heroes.html",
                           title="Heroes - Dotabank",
                           heroes_and_replay_counts=_heroes_and_replay_counts)


@hero_mod.route("/<string:_name>/")
@hero_mod.route("/<string:_name>/page/<int:page>")
def hero(_name, page=1):
    _hero = Hero.query.filter(Hero.name == _name).one()

    if _hero is None:
        abort(404)

    _replays = _hero.replays.\
        order_by(Replay.id.desc()).\
        paginate(page, current_app.config["REPLAYS_PER_PAGE"], False)

    return render_template("dota/hero.html",
                           title=u"{} - Dotabank".format(_hero.localized_name),
                           meta_description=u"Replays archived for {}".format(_hero.localized_name),
                           hero=_hero,
                           replays=_replays,
                           page=page)