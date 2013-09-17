from app import db
from flask.ext.login import current_user


# noinspection PyShadowingBuiltins
class Replay(db.Model):
    # TODO: date_added for ordering by date added to site (latest repalys on index)
    __tablename__ = "replays"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(80))
    local_uri = db.Column(db.String(128))
    state = db.Column(db.Enum(
        "WAITING_GC",
        "WAITING_DOWNLOAD",
        "DOWNLOAD_IN_PROGRESS",
        "WAITING_PARSE",
        "PARSE_IN_PROGRESS",
        "PARSED",
        "GC_ERROR",
        "PARSE_ERROR"
    ), default="WAITING_GC")
    replay_state = db.Column(db.Enum(
        "REPLAY_AVAILABLE",
        "REPLAY_NOT_RECORDED",
        "REPLAY_EXPIRED",
        "UNKNOWN"
    ), default="UNKNOWN")
    gc_fails = db.Column(db.Integer, default=0)

    ratings = db.relationship('ReplayRating', backref='replay', lazy='joined', cascade="all, delete-orphan")
    favourites = db.relationship('ReplayFavourite', backref='replay', lazy='joined', cascade="all, delete-orphan")
    combatlog = db.relationship('CombatLogMessage', order_by="asc(CombatLogMessage.timestamp)", backref='replay', lazy='dynamic', cascade="all, delete-orphan")

    def __init__(self, _id=None, url="", replay_state="UNKNOWN", state="WAITING_GC"):
        self.id = _id
        self.url = url
        self.replay_state = replay_state
        self.state = state

    def __repr__(self):
        return "<Replay {}>".format(self.id)

    def user_rating(self):
        if current_user.is_authenticated():
            return next((rating for rating in self.ratings if rating.user_id == current_user.id), None)
        else:
            return None

    def user_favourite(self):
        if current_user.is_authenticated():
            return next((favourite for favourite in self.favourites if favourite.user_id == current_user.id), False)
        else:
            return False


# noinspection PyShadowingBuiltins
class ReplayRating(db.Model):
    __tablename__ = "replay_ratings"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    positive = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, replay_id=None, user_id=None, positive=None):
        self.replay_id = replay_id
        self.user_id = user_id
        self.positive = positive

    def __repr__(self):
        return "<Rating {}/{}>".format(self.replay_id, self.user_id)


# noinspection PyShadowingBuiltins
class ReplayFavourite(db.Model):
    __tablename__ = "replay_favs"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    def __init__(self, replay_id=None, user_id=None):
        self.replay_id = replay_id
        self.user_id = user_id

    def __repr__(self):
        return "<Favourite {}/{}>".format(self.replay_id, self.user_id)


class CombatLogMessage(db.Model):
    __tablename__ = "combatlog_msgs"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=False)

    timestamp = db.Column(db.Float, nullable=False)
    tick = db.Column(db.Integer, nullable=False)

    type = db.Column(db.String(16), nullable=False)
    source_name = db.Column(db.String(80), nullable=False)
    target_name = db.Column(db.String(80), nullable=False)
    attacker_name = db.Column(db.String(80), nullable=False)
    inflictor_name = db.Column(db.String(80), nullable=False)
    attacker_illusion = db.Column(db.Boolean, nullable=False)
    target_illusion = db.Column(db.Boolean, nullable=False)
    target_source_name = db.Column(db.String(80), nullable=False)
    value = db.Column(db.Integer)
    health = db.Column(db.Integer)

    def __init__(self, replay_id, timestamp, tick, type, source_name, target_name, attacker_name, inflictor_name, attacker_illusion, target_illusion, value, health, target_source_name):
        self.replay_id = replay_id
        self.timestamp = timestamp
        self.tick = tick
        self.type = type
        self.source_name = source_name
        self.target_name = target_name
        self.attacker_name = attacker_name
        self.inflictor_name = inflictor_name
        self.attacker_illusion = attacker_illusion
        self.target_illusion = target_illusion
        self.target_source_name = target_source_name
        self.value = value
        self.health = health
