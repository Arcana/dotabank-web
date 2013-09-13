from app import app, db, admin
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.wtf import PasswordField
from flask.ext.login import current_user
from models import User, Replay, ReplayRating, ReplayFavourite, GCWorker, GCJob
from aes import AESCipher


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


class GCWorkerAdmin(AdminModelView):
    form_excluded_columns = ('password', 'sentry')
    column_exclude_list = ('password', 'sentry')

    def __init__(self, session):
        # Just call parent class with predefined model.
        super(GCWorkerAdmin, self).__init__(GCWorker, session)

    def scaffold_form(self):
        form_class = super(GCWorkerAdmin, self).scaffold_form()
        form_class.new_password = PasswordField('New Password')

        return form_class

    def on_model_change(self, form, model):
        if len(model.new_password):
            model.password = AESCipher(app.config["ENCRYPTION_KEY"]).encrypt(model.new_password)


admin.add_view(UserAdmin(db.session))
admin.add_view(ReplayAdmin(db.session))
admin.add_view(AdminModelView(ReplayRating, db.session))
admin.add_view(AdminModelView(ReplayFavourite, db.session))
admin.add_view(GCWorkerAdmin(db.session))
admin.add_view(AdminModelView(GCJob, db.session))
