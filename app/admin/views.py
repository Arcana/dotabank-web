from flask import Blueprint, g, current_app, redirect, request, flash, url_for
from flask.ext.admin import Admin, expose, AdminIndexView, BaseView
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user

from sqlalchemy.sql import text
from datetime import datetime, timedelta
from math import ceil

from app import db
from app.models import Log
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


class AtypicalReplays(AuthMixin, BaseView):
    @expose('/')
    def index(self):
        human_players_discrepancy = [x for x in db.engine.execute(
            text("""
                SELECT
                    r.id,
                    r.human_players,
                    count(*) as player_count
                FROM {replay_table} r
                LEFT JOIN {player_table} rp ON rp.replay_id = r.id
                WHERE
                    rp.account_id is not NULL  # Exclude bots from count (though there's the chance we have duplicate entries for bots? fack)
                GROUP BY rp.replay_id
            """.format(
                replay_table=Replay.__tablename__,
                player_table=ReplayPlayer.__tablename__)
            )
        ) if x.player_count != x.human_players]

        return self.render(
            'admin/atypical_replays.html',
            human_players_discrepancy=human_players_discrepancy
        )


class Logs(AuthMixin, BaseView):
    @expose('/')
    def index(self):
        unresolved_logs = Log.query.filter(Log.resolved_by_user_id == None).limit(current_app.config['LOGS_PER_PAGE']).all()
        unresolved_count = Log.query.filter(Log.resolved_by_user_id == None).count()

        resolved_logs = Log.query.filter(Log.resolved_by_user_id != None).limit(current_app.config['LOGS_PER_PAGE']).all()
        resolved_count = Log.query.filter(Log.resolved_by_user_id != None).count()

        return self.render(
            'admin/logs/index.html',
            unresolved_logs=unresolved_logs,
            unresolved_count=unresolved_count,
            resolved_logs=resolved_logs,
            resolved_count=resolved_count
        )

    @expose('/unresolved')
    @expose('/unresolved/<int:page>')
    def unresolved(self, page=None):
        if not page:
            page = int(ceil(float(Log.query.filter(Log.resolved_by_user_id == None).count() or 1) / float(current_app.config["LOGS_PER_PAGE"])))  # Default to last page

        logs = Log.query.filter(Log.resolved_by_user_id == None).paginate(page, current_app.config["LOGS_PER_PAGE"], False)

        return self.render(
            'admin/logs/unresolved.html',
            logs=logs
        )

    @expose('/resolved')
    @expose('/resolved/<int:page>')
    def resolved(self, page=None):
        if not page:
            page = int(ceil(float(Log.query.filter(Log.resolved_by_user_id != None).count() or 1) / float(current_app.config["LOGS_PER_PAGE"])))  # Default to last page

        logs = Log.query.filter(Log.resolved_by_user_id != None).paginate(page, current_app.config["LOGS_PER_PAGE"], False)

        return self.render(
            'admin/logs/resolved.html',
            logs=logs
        )

    @expose('/view/<int:_id>')
    def view(self, _id):
        log_entry = Log.query.filter(Log.id == _id).first_or_404()

        return self.render(
            'admin/logs/view.html',
            log=log_entry
        )

    @expose('/views/<int:_id>/resolve')
    def mark_resolved(self, _id):
        log_entry = Log.query.filter(Log.id == _id).first_or_404()

        log_entry.resolve(current_user.id)
        db.session.add(log_entry)
        db.session.commit()

        flash("Log entry {} marked as resolved.".format(log_entry.id), "success")
        return redirect(request.referrer or url_for("index"))

admin = Admin(name="Dotabank", index_view=AdminIndex())
admin.add_view(AtypicalReplays(name="Atypical Replays", category='Reports'))
admin.add_view(Logs(name="Logs", category="Reports"))


@mod.before_app_request
def before_request():
    if current_user.is_admin():
        g.admin = admin  # Only utilized under is_admin condition


# TODO: Toolbar stuffs
# - DebugToolbar kinda things; cpu time, sql queries, cache speed (though we don't cache anything yet)
