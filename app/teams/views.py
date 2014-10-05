from flask import Blueprint, render_template, current_app, abort, url_for
from app.replays.models import Replay
from sqlalchemy import or_


mod = Blueprint("teams", __name__, url_prefix="/teams")


@mod.route('/')
@mod.route("/page/<int:page>")
def teams(page=1):
    """ Render a list of teams, sorted by the amount of replays we have archived for each team. """
    # TODO
    return None

@mod.route("/<int:_id>/")
@mod.route("/<int:_id>/page/<int:page>")
def team(_id, page=1):

    _replays = Replay.query.filter(or_(Replay.radiant_team_id == _id, Replay.dire_team_id == _id)).order_by(Replay.id.desc()).paginate(page, current_app.config["REPLAYS_PER_PAGE"])
    if _replays.total <= 0:
        abort(404)

    _team = {
        'id': _id,
        'name': _replays.items[0].radiant_team_name if _replays.items[0].radiant_team_id == _id else _replays.items[0].dire_team_name,
        'logo': url_for('ugcfile', _id=_replays.items[0].radiant_team_logo) if _replays.items[0].radiant_team_id == _id else url_for('ugcfile', _id=_replays.items[0].dire_team_logo)
    }

    return render_template("teams/team.html",
                           title=u"{} replays - Dotabank".format(_team['name']),
                           meta_description=u"{} replays archived on Dotabank".format(_team['name']),
                           team=_team,
                           replays=_replays)
