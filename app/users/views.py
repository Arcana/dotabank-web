from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app

from app import oid, steam, db, login_manager
from models import User, AnonymousUser
from flask.ext.login import login_user, logout_user, current_user, login_required
from app.admin.views import AdminModelView

mod = Blueprint("users", __name__, url_prefix="/users")

login_manager.anonymous_user = AnonymousUser

# User authentication

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.update_last_seen()
    return user


@mod.route('/login/')
@oid.loginhandler
def login():
    if current_user.is_authenticated():
        return redirect(oid.get_next_url())
    return oid.try_login('http://steamcommunity.com/openid')


@oid.after_login
def create_or_login(resp):
    steam_id = long(resp.identity_url.replace("http://steamcommunity.com/openid/id/", ""))
    account_id = int(steam_id & 0xFFFFFFFF)
    user = User.query.filter(User.id == int(account_id & 0xFFFFFFFF)).first()

    if not user:
        user = User(int(account_id & 0xFFFFFFFF), steam.user.profile(steam_id).persona or account_id)

        db.session.add(user)
        db.session.commit()

    login_attempt = login_user(user)
    if login_attempt is True:
        flash("You are logged in as {}".format(user.name), "success")
    elif not user.is_active():
        flash("Cannot log you in as {}, your account has been disabled.  If you believe this is in error, please contact {}.".format(user.name, current_app.config["CONTACT_EMAIL"]), "danger")
    else:
        flash("Error logging you in as {}, please try again later.".format(user.name), "danger")
    return redirect(oid.get_next_url())


@mod.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(oid.get_next_url())


@mod.route("/")
@mod.route("/page/<int:page>/")
def users(page=1):
    if not current_user.is_admin():
        flash("User list is admin only atm.", "danger")
        return redirect(request.referrer or url_for("index"))
    users = User.query.paginate(page, current_app.config["USERS_PER_PAGE"], False)
    return render_template("users/users.html", users=users)


@mod.route("/<int:_id>/")
def user(_id):
    user = User.query.filter(User.id == _id).first()
    if user is None:
        flash("User {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))
    return render_template("users/user.html", user=user)


class UserAdmin(AdminModelView):
    column_display_pk = True
    form_columns = ('id', 'name', 'enabled')

    def __init__(self, session, **kwargs):
        # Just call parent class with predefined model.
        super(UserAdmin, self).__init__(User, session, **kwargs)
