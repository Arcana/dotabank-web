from flask import Blueprint, render_template, current_app, abort, url_for
from flask.ext.login import login_required, current_user
from models import Subscription

mod = Blueprint("subscriptions", __name__, url_prefix="/subscriptions")


@mod.route('/')
def marketing_bullshit():
    """ Our subscriptions are SO amazing you should DEFINITELY buy ALL of them at the SAME TIME. """
    return render_template("subscriptions/marketing_bullshit.html")


@mod.route('/my_subscription/')
@login_required
def my_subscription():
    # TODO: Make a User model method "get_active_subscription" and "get_all_subscriptions".
    current_subscription = current_user.get_active_subscription()
    all_subscriptions = current_user.subscriptions.all()

    return render_template("subscriptions/my_subscription.html",
                           current_subscription=current_subscription,
                           all_subscriptions=all_subscriptions,
                           user=current_user)
