from flask import Blueprint, g
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
        match_requests_capacity = GCWorker.query.count() * 100
        match_requests_past_24hrs = GCJob.query.filter(GCJob.timestamp >= (datetime.utcnow() - timedelta(hours=24))).count()

        return self.render('admin/index.html',
                           match_requests_capacity=match_requests_capacity,
                           match_requests_past_24hrs=match_requests_past_24hrs)


admin = Admin(name="Dotabank", index_view=AdminIndex())


@mod.before_app_request
def before_request():
    if current_user.is_admin():
        g.admin = admin  # Only utilized under is_admin condition


# TODO: Toolbar stuffs
# - DebugToolbar kinda things; cpu time, sql queries, cache speed (though we don't cache anything yet)
