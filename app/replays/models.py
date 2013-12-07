from app import db
from flask.ext.login import current_user
import datetime


# noinspection PyShadowingBuiltins
class Replay(db.Model):
    __tablename__ = "replays"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(80))
    local_uri = db.Column(db.String(128))
    state = db.Column(db.Enum(
        "WAITING_GC",
        "WAITING_DOWNLOAD",
        "DOWNLOAD_IN_PROGRESS",
        "ARCHIVED",
        "GC_ERROR",
        "DOWNLOAD_ERROR"
    ), default="WAITING_GC")
    replay_state = db.Column(db.Enum(
        "REPLAY_AVAILABLE",
        "REPLAY_NOT_RECORDED",
        "REPLAY_EXPIRED",
        "UNKNOWN"
    ), default="UNKNOWN")
    gc_fails = db.Column(db.Integer, default=0)
    dl_fails = db.Column(db.Integer, default=0)

    # Timestamps for progress tracker
    added_to_site_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    gc_done_time = db.Column(db.DateTime)
    dl_done_time = db.Column(db.DateTime)

    ratings = db.relationship('ReplayRating', backref='replay', lazy='joined', cascade="all, delete-orphan")
    favourites = db.relationship('ReplayFavourite', backref='replay', lazy='joined', cascade="all, delete-orphan")
    players = db.relationship('ReplayPlayer', backref="replay", lazy="dynamic", cascade="all, delete-orphan")
    downloads = db.relationship('ReplayDownload', backref="replay", lazy="dynamic", cascade="all, delete-orphan")

    # Set default order by
    __mapper_args__ = {
        "order_by": [db.desc(added_to_site_time)]
    }

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


# noinspection PyShadowingBuiltins
class ReplayDownload(db.Model):
    __tablename__ = "replay_downloads"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    def __init__(self, replay_id=None, user_id=None):
        self.replay_id = replay_id
        self.user_id = user_id

    def __repr__(self):
        return "<Download {}/{}>".format(self.replay_id, self.user_id)


# TODO: Revise to simple info, no snapshots.
class ReplayPlayer(db.Model):
    __tablename__ = "replay_players"

    id = db.Column(db.Integer, primary_key=True)
    replay_id = db.Column(db.Integer, db.ForeignKey("replays.id", ondelete="CASCADE"), nullable=False)

    # name = Column(String()) # Player name, we don't need to store this.
    steam_id = db.Column(db.BigInteger)
    team = db.Column(db.Enum("radiant", "dire", "spectator"))
    index = db.Column(db.Integer)

    def __init__(self, replay_id, steam_id, team, index):
        self.replay_id = replay_id
        self.steam_id = steam_id
        self.team = team
        self.index = index

    def __repr__(self):
        return "<ReplayPlayer {}>".format(self.id)
