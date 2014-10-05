from flask import Blueprint, render_template, current_app, abort, url_for

mod = Blueprint("subscriptions", __name__, url_prefix="/subscriptions")


@mod.route('/')
def marketing_bullshit():
    """ Our subscriptions are SO amazing you should DEFINITELY buy ALL of them at the SAME TIME. """
    return render_template("subscriptions/marketing_bullshit.html")
