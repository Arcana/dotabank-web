from flask import Blueprint, g, current_app
from flask.ext.admin import Admin, expose, AdminIndexView
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user

from datetime import datetime, timedelta

from app.gc.models import GCJob, GCWorker

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
                "match_requests_capacity": current_app.config['GC_MATCH_REQUSTS_RATE_LIMIT'],
                "profile_requests_past_24hrs": GCJob.query.filter(
                    GCJob.worker_id == worker.id,
                    GCJob.type == "PROFILE_REQUEST",
                    GCJob.timestamp >= (datetime.utcnow() - timedelta(hours=24))
                ).count(),
                "profile_requests_capacity": current_app.config['GC_PROFILE_REQUSTS_RATE_LIMIT']
            })

        return self.render('admin/index.html',
                           stats=stats)


admin = Admin(name="Dotabank", index_view=AdminIndex())


@mod.before_app_request
def before_request():
    if current_user.is_admin():
        g.admin = admin  # Only utilized under is_admin condition


# TODO: Toolbar stuffs
# - DebugToolbar kinda things; cpu time, sql queries, cache speed (though we don't cache anything yet)
