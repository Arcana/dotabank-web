from flask import Blueprint, render_template, current_app, abort
from app.replays.models import Replay
from sqlalchemy import or_


mod = Blueprint("teams", __name__, url_prefix="/teams")
@mod.route("/<int:_id>/")
@mod.route("/<int:_id>/page/<int:page>")
def team(_id, page=1):

    _replays = Replay.query.filter(or_(Replay.radiant_team_id == _id, Replay.dire_team_id == _id)).order_by(Replay.id.desc()).paginate(page, current_app.config["REPLAYS_PER_PAGE"])
    if _replays.total <= 0:
        abort(404)
    team_found = False
    loop_num = 0
    while not team_found:
        if _replays.items[loop_num].radiant_team_id == _id:
            _team = {'id': _id,
                     'name': _replays.items[loop_num].radiant_team_name,
                     'logo': _replays.items[loop_num].radiant_team_logo}
            team_found = True
        loop_num += 1

    return render_template("teams/team.html",
                           title="{} replays - Dotabank".format(_team['name']),
                           team=_team,
                           replays=_replays)