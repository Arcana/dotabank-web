from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app, g

from app import oid, db, login_manager, mem_cache
from models import User, AnonymousUser
from app.replays.models import ReplayPlayer, ReplayFavourite, ReplayRating, ReplayDownload, Search, ReplayAlias
from app.dota.models import Localization
from forms import SettingsForm
from flask.ext.login import login_user, logout_user, current_user, login_required
from app.admin.views import AdminModelView
from math import ceil
from sqlalchemy.exc import IntegrityError

mod = Blueprint("users", __name__, url_prefix="/users")

login_manager.anonymous_user = AnonymousUser


# User authentication
@login_manager.user_loader
def load_user(user_id):
    name_updated_key = 'league_info_updated_{}'.format(user_id)
    name_lock_key = 'league_info_update_lock_{}'.format(user_id)

    _user = User.query.filter(User.id == user_id).outerjoin(User.replay_aliases).first()
    if _user:
        _user.update_last_seen()

        # Update the user's Steam name once per hour.
        if not mem_cache.get(name_updated_key) and not mem_cache.get(name_lock_key):
            _user.update_steam_name()

        # Load replay_aliases for current user for easy alias-grabbing. (faster than a new query for every replay)
        _user.replay_aliases_dict = {x.replay_id: x for x in _user.replay_aliases}

        if not _user.is_active():
            logout_user()
    return _user


@mod.before_app_request
def add_user_to_globals():
    g.user = current_user


@mod.before_app_request
def load_dota_localization():
    g.localization = Localization(current_user.get_language())


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
    _user = User.query.filter(User.id == int(account_id & 0xFFFFFFFF)).first()

    if not _user:
        _user = User(int(account_id & 0xFFFFFFFF), account_id)
        _user.update_steam_name()

        try:
            db.session.add(_user)
            db.session.commit()
        except IntegrityError:
            pass  # User already in database, likely a race condition on registration.

    login_attempt = login_user(_user)
    if login_attempt is True:
        flash(u"You are logged in as {}".format(_user.name), "success")
    elif not _user.is_active():
        flash(u"Cannot log you in as {}, your account has been disabled.  If you believe this is in error, please contact {}.".format(_user.name, current_app.config["CONTACT_EMAIL"]), "danger")
    else:
        flash(u"Error logging you in as {}, please try again later.".format(_user.name), "danger")
    return redirect(oid.get_next_url())


#@mod.route('/shittytest/')
#def shitty_test():
#    _users = User.query.all()
#
#    for _user in _users:
#        flash(u"FUCKING USER {}".format(_user.name), "success")
#
#    return redirect(url_for('index'))


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
    _users = User.query.paginate(page, current_app.config["USERS_PER_PAGE"], False)
    return render_template("users/users.html",
                           title="Users - Dotabank",
                           users=_users)


@mod.route("/<int:_id>/")
def user(_id):
    _user = User.query.filter(User.id == _id).first()
    limit = current_app.config["USER_OVERVIEW_LIMIT"]
    if _user is None:
        flash("User {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))
    _replays = _user.replay_players.order_by(False).order_by(ReplayPlayer.replay_id.desc()).limit(limit)
    _favourites = _user.favourites.order_by(False).order_by(ReplayFavourite.created_at.desc()).limit(limit)
    _searches = _user.searches.order_by(False).order_by(Search.created_at.desc()).limit(limit)
    _downloads = _user.downloads.order_by(False).order_by(ReplayDownload.created_at.desc()).limit(limit)
    _ratings = _user.replay_ratings.order_by(False).order_by(ReplayRating.created_at.desc()).limit(limit)
    _aliases = _user.replay_aliases.order_by(False).order_by(ReplayAlias.updated_at.desc()).limit(limit)
    return render_template("users/user.html",
                           title=u"{} - Dotabank".format(_user.name),
                           user=_user,
                           replays=_replays,
                           favourites=_favourites,
                           searches=_searches,
                           downloads=_downloads,
                           ratings=_ratings,
                           aliases=_aliases)


@mod.route("/<int:_id>/replays/")
@mod.route("/<int:_id>/replays/<int:page>/")
def user_replays(_id, page=None):
    _user = User.query.filter(User.id == _id).first()
    if _user is None:
        flash("User {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))
    if not page:
        page = int(ceil(float(ReplayPlayer.query.filter(ReplayPlayer.account_id == _user.id).count() or 1) / float(current_app.config["REPLAYS_PER_PAGE"])))  # Default to last page
    _replays = _user.replay_players.paginate(page, current_app.config["REPLAYS_PER_PAGE"], False)
    return render_template("users/replays.html",
                           title=u"{}'s replays - Dotabank".format(_user.name),
                           user=_user,
                           replays=_replays)


@mod.route("/<int:_id>/favourites/")
@mod.route("/<int:_id>/favourites/<int:page>/")
def user_favourites(_id, page=None):
    _user = User.query.filter(User.id == _id).first()
    if _user is None:
        flash("User {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))
    if not page:
        page = int(ceil(float(ReplayFavourite.query.filter(ReplayFavourite.user_id == _user.id).count() or 1) / float(current_app.config["REPLAYS_PER_PAGE"])))  # Default to last page
    _favourites = _user.favourites.paginate(page, current_app.config["REPLAYS_PER_PAGE"], False)
    return render_template("users/favourites.html",
                           title=u"{}'s favourites - Dotabank".format(_user.name),
                           user=_user,
                           favourites=_favourites)


@mod.route("/<int:_id>/ratings/")
@mod.route("/<int:_id>/ratings/<int:page>/")
def user_ratings(_id, page=None):
    _user = User.query.filter(User.id == _id).first()
    if _user is None:
        flash("User {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))
    if not page:
        pass
    page = int(ceil(float(ReplayRating.query.filter(ReplayRating.user_id == _user.id).count() or 1) / float(current_app.config["REPLAYS_PER_PAGE"])))  # Default to last page
    _ratings = _user.replay_ratings.paginate(page, current_app.config["REPLAYS_PER_PAGE"], False)
    return render_template("users/ratings.html",
                           title=u"{}'s ratings - Dotabank".format(_user.name),
                           user=_user,
                           ratings=_ratings)


@mod.route("/<int:_id>/searches/")
@mod.route("/<int:_id>/searches/<int:page>/")
def user_searches(_id, page=None):
    _user = User.query.filter(User.id == _id).first()
    if _user is None:
        flash("User {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))
    if not page:
        page = int(ceil(float(Search.query.filter(Search.user_id == _user.id).count() or 1) / float(current_app.config["REPLAYS_PER_PAGE"])))  # Default to last page
    _searches = _user.searches.paginate(page, current_app.config["REPLAYS_PER_PAGE"], False)
    return render_template("users/searches.html",
                           title=u"{}'s searches - Dotabank".format(_user.name),
                           user=_user,
                           searches=_searches)


@mod.route("/<int:_id>/downloads/")
@mod.route("/<int:_id>/downloads/<int:page>/")
def user_downloads(_id, page=None):
    _user = User.query.filter(User.id == _id).first()
    if _user is None:
        flash("User {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))
    if not page:
        page = int(ceil(float(ReplayDownload.query.filter(ReplayDownload.user_id == _user.id).count() or 1) / float(current_app.config["REPLAYS_PER_PAGE"])))  # Default to last page
    _downloads = _user.downloads.paginate(page, current_app.config["REPLAYS_PER_PAGE"], False)
    return render_template("users/downloads.html",
                           title=u"{}'s downloads - Dotabank".format(_user.name),
                           user=_user,
                           downloads=_downloads)


@mod.route("/<int:_id>/aliases/")
@mod.route("/<int:_id>/aliases/<int:page>/")
def user_aliases(_id, page=None):
    _user = User.query.filter(User.id == _id).first_or_404()

    if not page:
        page = int(ceil(float(ReplayAlias.query.filter(ReplayAlias.user_id == _user.id).count() or 1) / float(current_app.config["REPLAYS_PER_PAGE"])))  # Default to last page

    _aliases = _user.replay_aliases.paginate(page, current_app.config["REPLAYS_PER_PAGE"], False)
    return render_template("users/aliases.html",
                           title=u"{}'s aliases - Dotabank".format(_user.name),
                           user=_user,
                           aliases=_aliases)


@mod.route("/<int:_id>/update_name")
@login_required
def update_name(_id):
    # Check auth
    if not current_user.is_admin():
        flash("Only admins can force-update user names.", "danger")
        return redirect(request.referrer or url_for("index"))

    # Get user
    _user = User.query.filter(User.id == _id).first()
    if _user is None:
        flash("User {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    old_name = _user.name
    _user.update_steam_name()
    new_name = _user.name

    current_app.logger.info("Manually triggered a user name update.", extra={
        'extra': {
            'old_name': old_name,
            'new_name': new_name,
            'actioned_by': current_user.id
        }
    })

    flash(u"Updated user {}'s name from {} to {}.".format(_id, old_name, new_name), "success")
    return redirect(request.referrer or url_for("index"))


@mod.route("/<int:_id>/settings/", methods=["POST", "GET"])
@login_required
def settings(_id):
    # Authentication
    if current_user.id != _id and not current_user.is_admin():
        flash("You are not authorised to edit user {}'s settings.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    # Check user exists
    _user = User.query.filter(User.id == _id).first()
    if _user is None:
        flash("User {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    # Validate form, if submitted; else render it.
    form = SettingsForm(_user, request.form)

    if form.validate_on_submit():
        _user.email = form.email.data
        _user.show_ads = form.show_ads.data
        db.session.add(_user)
        db.session.commit()

        # If we have a customer on Stripe associated with this user then update the Stripe customer's invoice email address
        stripe_customer = _user.get_stripe_customer()
        if stripe_customer is not None:
            stripe_customer.email = _user.email
            stripe_customer.save()

        return redirect(request.args.get("next") or url_for("users.user", _id=_user.id))

    return render_template("users/settings.html",
                           title="Your settings - Dotabank",
                           user=_user,
                           form=form)


class UserAdmin(AdminModelView):
    column_display_pk = True

    def __init__(self, session, **kwargs):
        # Just call parent class with predefined model.
        super(UserAdmin, self).__init__(User, session, **kwargs)
