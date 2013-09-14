from flask import Blueprint, g
from flask.ext.admin import Admin, expose, AdminIndexView
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.login import current_user

mod = Blueprint("dotabank_admin", __name__)


class AuthMixin(object):
    def is_accessible(self):
        return current_user.is_admin()


class AdminModelView(AuthMixin, ModelView):
    pass


class AdminIndex(AuthMixin, AdminIndexView):
    @expose("/")
    def index(self):
        return self.render('admin/index.html', blorg="lblrlbleblorg")


admin = Admin(name="Dotabank", index_view=AdminIndex())


@mod.before_app_request
def before_request():
    if current_user.is_admin():
        g.admin = admin  # Only utilized under is_admin condition
