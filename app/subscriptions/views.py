from flask import Blueprint, render_template, current_app, abort, url_for, request, redirect, flash
from flask.ext.login import login_required, current_user
from app import db
from models import Subscription
import stripe

mod = Blueprint("subscriptions", __name__, url_prefix="/subscriptions")


@mod.route('/')
def marketing_bullshit():
    """ Our subscriptions are SO amazing you should DEFINITELY buy ALL of them at the SAME TIME. """
    return render_template("subscriptions/marketing_bullshit.html")


@mod.route('/my_subscription/')
@login_required
def my_subscription():
    current_subscription = current_user.get_active_subscription()
    all_subscriptions = current_user.subscriptions.all()

    customer = current_user.get_stripe_customer()

    return render_template("subscriptions/my_subscription.html",
                           current_subscription=current_subscription,
                           all_subscriptions=all_subscriptions,
                           customer=customer,
                           user=current_user)

@mod.route('/update_card/', methods=["POST"])
@login_required
def update_card():
    input_email = request.form.get('updateCardDetailsEmail')
    input_token = request.form.get('updateCardDetailsToken')

    if not input_email:
        flash("Sorry, you must provide an e-mail address to update your card details.", "danger")
        return redirect(request.referrer or url_for("index"))

    if not input_token:
        flash("Sorry, there was a problem saving your card details. Please try again", "danger")
        return redirect(request.referrer or url_for("index"))

    # Create or update Stripe customer
    customer = current_user.get_stripe_customer()

    if customer is None:
        customer = stripe.Customer.create(
            description="Dotabank.com customer {}".format(current_user.get_id()),
            metadata={
                'user_id': current_user.get_id()
            }
        )

    # Save card token
    customer.email = input_email
    customer.card = input_token
    customer.save()

    # Save or update user email address
    current_user.stripe_id = customer.id
    current_user.email = input_email
    db.session.add(current_user)
    db.session.commit()

    # Return to origin
    flash("Updated card details", "success")
    return redirect(request.referrer or url_for("index"))