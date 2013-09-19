from app import app
from app.admin.views import AdminModelView
from wtforms import PasswordField
from models import GCWorker
from helpers import AESCipher


class GCWorkerAdmin(AdminModelView):
    form_excluded_columns = ('password', 'sentry')
    column_exclude_list = ('password', 'sentry')

    def __init__(self, session, **kwargs):
        # Just call parent class with predefined model.
        super(GCWorkerAdmin, self).__init__(GCWorker, session, **kwargs)

    def scaffold_form(self):
        form_class = super(GCWorkerAdmin, self).scaffold_form()
        form_class.new_password = PasswordField('New Password')

        return form_class

    def on_model_change(self, form, model):
        if len(model.new_password):
            model.password = AESCipher(app.config["ENCRYPTION_KEY"]).encrypt(model.new_password)
