from app import db, steam
from flask.ext.login import AnonymousUserMixin
import datetime
from calendar import timegm as to_timestamp


# noinspection PyMethodMayBeStatic
class AnonymousUser(AnonymousUserMixin):
    def is_admin(self):
        return False

    def allows_ads(self):
        return True


# noinspection PyShadowingBuiltins
# noinspection PyMethodMayBeStatic
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(64), unique=False, nullable=True)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    first_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    admin = db.Column(db.Boolean, default=False)
    show_ads = db.Column(db.Boolean, default=True)

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
        # Called every page load for current_user (API is cached)
        steam_account_info = steam.user.profile(self.steam_id)
        try:
            if steam_account_info is not None:
                if self.name is not steam_account_info.persona:
                    self.name = steam_account_info.persona
                    db.session.add(self)
                    db.session.commit()
        except steam.api.HTTPError:
            pass

    def allows_ads(self):
        return self.show_ads

    @property
    def is_premium(self):
        subscription = self.subscriptions.filter(
            Subscription.expires_at >= datetime.datetime.utcnow()
        ).first()

        return bool(subscription)

    @property
    def steam_id(self):
        return self.id + User.ACCOUNT_ID_TO_STEAM_ID_CORRECTION


class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, user_id=None, created_at=None, expires_at=None):
        self.user_id = user_id
        self.created_at = created_at
        self.expires_at = expires_at

    def __repr__(self):
        return "<Subscription {}>".format(id)

    @property
    def created_at_timestamp(self):
        return to_timestamp(self.created_at.utctimetuple())


    @staticmethod
    def get_valid_subscriptions():
        return Subscription.query.filter(Subscription.expires_at >= datetime.datetime.utcnow()).all()


class SubscriptionLastMatch(db.Model):
    """
    Used for automatic match archiving.  Logs the last replay
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    replay_found = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, user_id=None, replay_found=None):
        self.user_id = user_id
        self.replay_found = replay_found

    def __repr__(self):
        return "SubscriptionLastMatch {}/{}>".format(self.user_id, self.created_at)

    @property
    def created_at_timestamp(self):
        return to_timestamp(self.created_at.utctimetuple())
