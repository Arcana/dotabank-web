import datetime
import stripe

from flask.ext.login import AnonymousUserMixin

from app import db, steam
from app.subscriptions.models import Subscription



# noinspection PyMethodMayBeStatic
class AnonymousUser(AnonymousUserMixin):
    def is_admin(self):
        return False

    def allows_ads(self):
        return True

    def get_language(self):  # TODO: When we do localization
        return "english"


# noinspection PyShadowingBuiltins
# noinspection PyMethodMayBeStatic
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(64), unique=False, nullable=True)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    first_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    last_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    admin = db.Column(db.Boolean, default=False)
    show_ads = db.Column(db.Boolean, default=True)

    stripe_id = db.Column(db.String(255))

    replay_ratings = db.relationship('ReplayRating', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    favourites = db.relationship('ReplayFavourite', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    downloads = db.relationship('ReplayDownload', backref="user", lazy="dynamic", cascade="all")
    subscriptions = db.relationship('Subscription', backref="user", lazy="dynamic", cascade="all")
    searches = db.relationship('Search', backref="user", lazy="dynamic", cascade="all")
    logs_resolved = db.relationship('Log', backref='resolved_by_user', lazy='dynamic', cascade='all')
    replay_aliases = db.relationship('ReplayAlias', backref='user', lazy='dynamic', cascade="all")

    replay_players = db.relationship('ReplayPlayer', backref='user', lazy='dynamic', order_by='ReplayPlayer.replay_id')

    # Set default order by
    __mapper_args__ = {
        "order_by": [db.asc(first_seen)]
    }

    ACCOUNT_ID_TO_STEAM_ID_CORRECTION = 76561197960265728

    def __init__(self, _id=None, name=None, enabled=True):
        self.id = _id
        self.name = name
        self.enabled = enabled

    def __repr__(self):
        return self.name

    def get_id(self):
        return unicode(self.id)

    def is_active(self):
        return self.enabled

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def is_admin(self):
        return self.admin

    def update_last_seen(self):
        # Called every page load for current_user
        self.last_seen = datetime.datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def update_steam_name(self):
        """ Update user's name from their name on Steam."""
        try:
            steam_account_info = steam.user.profile(self.steam_id)
            if steam_account_info is not None:
                if self.name != steam_account_info.persona:
                    self.name = steam_account_info.persona
                    db.session.add(self)
                    db.session.commit()
        except steam.api.SteamError:
            pass

    def allows_ads(self):
        return self.show_ads

    def get_language(self):  # TODO: When we do localization
        return "english"

    def get_active_subscription(self):
        return self.subscriptions.filter(
            Subscription.expires_at >= datetime.datetime.utcnow()
        ).first()

    def get_stripe_customer(self):
        if self.stripe_id is None:
            return None

        try:
            customer = stripe.Customer.retrieve(self.stripe_id)
            if not customer.get('deleted'):
                return customer
            else:
                return None
        except stripe.InvalidRequestError:
            return None

    @staticmethod
    def update_stripe_details(_user, stripe_customer, stripe_token, new_email=None):
        # Save card token
        if new_email is not None:
            stripe_customer.email = new_email
            _user.email = new_email

        stripe_customer.card = stripe_token
        stripe_customer.save()

        # Save or update user email address
        _user.stripe_id = stripe_customer.id
        db.session.add(_user)
        db.session.commit()

    @property
    def is_premium(self):
        subscription = self.subscriptions.filter(
            Subscription.expires_at >= datetime.datetime.utcnow()
        ).first()

        return bool(subscription)

    @property
    def steam_id(self):
        return self.id + User.ACCOUNT_ID_TO_STEAM_ID_CORRECTION


