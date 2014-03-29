from flask import Blueprint, g, current_app
from flask.ext.admin import Admin, expose, AdminIndexView, BaseView
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user

from sqlalchemy.sql import text
from datetime import datetime, timedelta

from app import db
from app.gc.models import GCJob, GCWorker
from app.replays.models import Replay, ReplayPlayer

mod = Blueprint("dotabank_admin", __name__)


#noinspection PyMethodMayBeStatic
class AuthMixin(object):
    def is_accessible(self):
        return current_user.is_admin()


class AdminModelView(AuthMixin, ModelView):
    pass


class AdminIndex(AuthMixin, AdminIndexView):
    @expose("/")
    def index(self):
        gc_workers = GCWorker.query.all()

        stats = []
        for worker in gc_workers:

            stats.append({
                "id": worker.id,
                "display_name": worker.display_name,
                "match_requests_past_24hrs": GCJob.query.filter(
                    GCJob.worker_id == worker.id,
                    GCJob.type == "MATCH_REQUEST",
                    GCJob.timestamp >= (datetime.utcnow() - timedelta(hours=24))
                ).count(),
                "match_requests_capacity": current_app.config['GC_MATCH_REQUSTS_RATE_LIMIT']
            })

        return self.render('admin/index.html',
                           stats=stats)


class Reports(BaseView):
    @expose('/')
    def index(self):
        replays_without_ten_players = [x for x in db.engine.execute(
            text("""
                SELECT
                    r.id,
                    count(*) as player_count
                FROM {replay_table} r
                LEFT JOIN {player_table} rp ON rp.replay_id = r.id
                WHERE
                    r.game_mode NOT IN (7, 9) # Disgard diretide (7)/greeviling (9)
                GROUP BY rp.replay_id
            """.format(
                replay_table=Replay.__tablename__,
                player_table=ReplayPlayer.__tablename__)
            )
        ) if x.player_count != 10]  # Do the "not-10" check in the app cause idfk how to do it in sql.

        return self.render(
            'admin/reports.html',
            replays_without_ten_players=replays_without_ten_players
        )

admin = Admin(name="Dotabank", index_view=AdminIndex())
admin.add_view(Reports(name='Reports'))


@mod.before_app_request
def before_request():
    if current_user.is_admin():
        g.admin = admin  # Only utilized under is_admin condition


# TODO: Toolbar stuffs
# - DebugToolbar kinda things; cpu time, sql queries, cache speed (though we don't cache anything yet)
