from flask import Blueprint, render_template, current_app, abort, url_for, request, redirect, flash
from flask.ext.login import login_required, current_user
from app import db
from models import Subscription
import stripe
from datetime import datetime, timedelta

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
                           user=current_user,
                           plans=sorted(Subscription.PLANS.iteritems(), key=lambda x: x[1]['amount']))


@mod.route('/update_card/', methods=["POST"])
@login_required
def update_card():
    input_email = request.form.get('updateCardDetailsEmail')
    input_token = request.form.get('updateCardDetailsToken')

    if not input_email:
        flash("Sorry, you must provide an e-mail address to update your card details.", "danger")
        return redirect(request.referrer or url_for("subscriptions.my_subscription"))

    if not input_token:
        flash("Sorry, there was a problem saving your card details. Please try again", "danger")
        return redirect(request.referrer or url_for("subscriptions.my_subscription"))

    # Create or update Stripe customer
    customer = current_user.get_stripe_customer()

    if customer is None:
        customer = stripe.Customer.create(
            description="Dotabank.com customer {}".format(current_user.get_id()),
            metadata={
                'user_id': current_user.get_id()
            }
        )

    # Update user's stripe and customer details
    current_user.update_stripe_details(current_user, customer, input_token, input_email)

    # Return to origin
    flash("Updated card details", "success")
    return redirect(request.referrer or url_for("index"))


@mod.route('/change_subscription/', methods=["POST"])
def change_subscription():
    """ Changes a user's subscription plan
    """
    input_subscription = request.form.get('newSubscription')
    cancel = bool(request.form.get('cancel'))
    input_email = request.form.get('newCardDetailsEmail')
    input_token = request.form.get('newCardDetailsToken')

    if cancel is False and (input_subscription is None or input_subscription not in Subscription.PLANS.keys()):
        flash("Sorry, there was an error setting your new subscription. Please try again", "danger")
        return redirect(request.referrer or url_for("subscriptions.my_subscription"))

    # Create or update Stripe customer
    customer = current_user.get_stripe_customer()

    if customer is None:
        if not input_token or not input_email:
            flash("Sorry, we don't have any payment details on record for you.  Please provide payment details in order"
                  "to subscribe.", "danger")
            return redirect(request.referrer or url_for("subscriptions.my_subscription"))
        else:
            customer = stripe.Customer.create(
                description="Dotabank.com customer {}".format(current_user.get_id()),
                metadata={
                    'user_id': current_user.get_id()
                }
            )

        # Update user's stripe and customer details
        current_user.update_stripe_details(current_user, customer, input_token, input_email)

    if cancel is True:  # TOAD TO: MAKE TEST
        # The subscriptions will remain active until it the end of the already-payed-for period ends.
        customer.subscriptions.retrieve().delete(at_period_end=True)
        flash("Cancelled your subscription.", "success")
        return redirect(request.referrer or url_for("index"))

    existing_subscription = current_user.get_active_subscription()
    new_expiry_date = datetime.utcnow() + timedelta(days=30)  # This will be updated by Stripe via webhooks, but we'll populate it here in case Stripe is slow (or we're testing locally)
    if existing_subscription:
        # Terminate early
        new_expiry_date = existing_subscription.expires_at  # New sub will end when the old sub billing period ends
        existing_subscription.expires_at = datetime.utcnow()
        db.session.add(existing_subscription)

    # Create a new subscription. `old_expiry_date` will be set if we're upgrading/downgrading an existing subscription.
    new_subscription = Subscription(current_user.get_id(), datetime.utcnow(), new_expiry_date, input_subscription, auto_renew=True)
    db.session.add(new_subscription)
    db.session.commit()

    customer.plan = input_subscription
    customer.save()
    flash("Saved your subscription!", "success")

    return redirect(request.referrer or url_for("index"))

