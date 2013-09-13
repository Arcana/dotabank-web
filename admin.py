from app import db
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user
from models import User, Replay, ReplayRating, ReplayFavourite, GCWorker, GCJob

admin = Admin(name="Dotabank")


class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_admin()


class UserAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ('id', 'name', 'enabled')

    def __init__(self, session):
        # Just call parent class with predefined model.
        super(UserAdmin, self).__init__(User, session)


class ReplayAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ("id", "url", "state", "replay_state")

    def __init__(self, session):
        # Just call parent class with predefined model.
        super(ReplayAdmin, self).__init__(Replay, session)

admin.add_view(UserAdmin(db.session))
admin.add_view(ReplayAdmin(db.session))
admin.add_view(AdminModelView(ReplayRating, db.session))
admin.add_view(AdminModelView(ReplayFavourite, db.session))
admin.add_view(AdminModelView(GCWorker, db.session))
admin.add_view(AdminModelView(GCJob, db.session))
